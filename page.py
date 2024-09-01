import json
import os
from ctypes import windll

import numpy as np
import win32gui
import win32ui
from pydantic import BaseModel, Field

from constants import Setting
from utils import refresh_setting, crop_image, SpecialPositionJson, timer, ocr, control


# 预设页面列表
listDictPages = [
    {
        "pageName": "主界面",
        "text": "战役推进",
        "route": [
            {
                "pageName": "剧情战役",
                "text": "战役推进",
            },
            {
                "pageName": "班组",
                "text": "班组",
            },
            {
                "pageName": "公共区",
                "text": "公共区",
            }
        ]
    },
    {
        "pageName": "班组",
        "text": "要务",
        "route": [
            {
                "pageName": "班组要务",
                "text": "要务",
            },
            {
                "pageName": "班组补给",
                "text": "补给",
            }
        ]
    }
]


class PositionModel(BaseModel):
    """
    位置模型
    """
    x1: int = Field(None, title="x1")
    y1: int = Field(None, title="y1")
    x2: int = Field(None, title="x2")
    y2: int = Field(None, title="y2")

    def __str__(self):
        return f"({self.x1}, {self.y1}, {self.x2}, {self.y2})"


class TextModel(BaseModel):
    """
    文本模型
    """
    text: str = Field("", title="文本")
    pos: PositionModel = Field(None, title="文本位置模型")

    def __str__(self):
        return f"文本：{self.text}, 位置：{self.modelPos}"


class PageRouteModel(TextModel):
    """
    页面转移路径模型
    """
    pageName: str = Field("", title="指向页面名称")

    def __str__(self):
        return f"下一界面名：{self.pageName}，指向文本：{self.text}"


class PageModel(TextModel):
    """
    页面模型
    """
    pageName: str = Field("", title="页面名称")
    route: list = Field([], title="下一界面路径模型列表")

    def __str__(self):
        return f"页面名称：{self.pageName}，特征文本：{self.text}，下一界面路径列表：{self.route}"


def get_dictPages():
    """
    获取页面模型列表
    :return: 页面模型字典，字典键为页面名称，值为PageModel对象
    """
    _dictPages = {}  # 初始化全页面
    for dictPage in listDictPages:
        # 检索是否存在该页面json文件
        try:  # 存在该页面json文件
            with open('page/' + dictPage['pageName'] + '.json', 'r', encoding='utf-8') as file:
                data = json.load(file)

            # text = data['text']
            # pos = PositionModel(**data['pos'])
            # for index, dictPageRoute in enumerate(data['route']):
            #
            #     data['route'][index] = PageRouteModel(**dictPageRoute)
            #
            # dictPage = PageModel(
            #     text=text,
            #     pos=pos,
            #     route=data['route']
            # )
            dictPage = data

        except FileNotFoundError:  # 不存在该页面json文件
            pass

        finally:
            # 创建次级界面模型列表
            listPageRoute = []
            for pageRoute in dictPage['route']:
                pageRouteModel = PageRouteModel(**pageRoute)
                listPageRoute.append(pageRouteModel)

            dictPage['route'] = listPageRoute
            _dictPages[dictPage['pageName']] = PageModel(**dictPage)

    return _dictPages


def screenshot():
    """
    截图
    ：return: 截取到的图像np数组
    """
    hwndDC = win32gui.GetWindowDC(Setting.hwnd)  # 获取窗口设备上下文（DC）
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)  # 创建mfcDC
    saveDC = mfcDC.CreateCompatibleDC()  # 创建与mfcDC兼容的DC
    saveBitMap = win32ui.CreateBitmap()  # 创建一个位图对象
    saveBitMap.CreateCompatibleBitmap(mfcDC, Setting.screenWidth, Setting.screenHeight)  # 创建与mfcDC兼容的位图
    saveDC.SelectObject(saveBitMap)  # 选择saveDC的位图对象，准备绘图
    # 尝试使用PrintWindow函数截取窗口图像
    windll.user32.PrintWindow(Setting.hwnd, saveDC.GetSafeHdc(), 3)

    # 从位图中获取图像数据
    bmp_info = saveBitMap.GetInfo()  # 获取位图信息
    bmp_str = saveBitMap.GetBitmapBits(True)  # 获取位图数据
    im = np.frombuffer(bmp_str, dtype="uint8")  # 将位图数据转换为numpy数组
    im.shape = (bmp_info["bmHeight"], bmp_info["bmWidth"], 4)  # 设置数组形状
    # 调整通道顺序并去除alpha通道
    im = im[:, :, :3]
    im = im[:, :, [2, 1, 0]]

    # 清理资源
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(Setting.hwnd, hwndDC)

    return im  # 返回截取到的图像


class OCRResultError(Exception):
    """
    OCR识别结果异常
    """
    pass


def ocr_textAll(image):
    """
    识别图像中的所有文字
    """
    listResults = ocr(image)[0]
    if len(listResults) == 0:  # 检测不到文字报错
        raise OCRResultError("未识别出文字")

    listTextModel = []
    for result in listResults:
        confidence = result[2]
        if confidence > Setting.threshold:
            text = result[1]
            box = result[0]
            modelPos = PositionModel(
                x1=box[0][0],
                y1=box[0][1],
                x2=box[2][0],
                y2=box[2][1]
            )
            modelText = TextModel(text=text, pos=modelPos)
            listTextModel.append(modelText)

    return listTextModel


def ocr_crop(image, modelText: TextModel):
    """
    裁剪图像识别文字
    :param image: 原图像，用以裁剪
    :param modelText: 文字模型
    :return: 识别结果
    """
    pos = modelText.pos
    posEnlarged = PositionModel(
        x1=pos.x1 - Setting.enlarge,
        y1=pos.y1 - Setting.enlarge,
        x2=pos.x2 + Setting.enlarge,
        y2=pos.y2 + Setting.enlarge
    )
    imageCrop = image[posEnlarged.y1:posEnlarged.y2, posEnlarged.x1:posEnlarged.x2]
    return ocr_textAll(imageCrop)


def record_pageJson(modelPage):
    """
    将页面特征写入json文件
    """
    data = modelPage.json()  # 获取页面特征json
    with open('page/' + modelPage.pageName + '.json', 'w', encoding='utf-8') as file:
        file.write(data)  # 写入json文件


def get_signRecordPos(modelPage) -> bool:
    """
    决定是否记录页面特征
    :param modelPage: 页面模型
    :return: 是否记录页面特征位置
    """
    if not modelPage.pos:  # 页面特征位置未记录
        return True

    for modelPageRoute in modelPage.route:
        if not modelPageRoute.pos:  # 次级页面特征位置未记录
            return True

    return False


class UnknownPage(Exception):
    """
    未知页面异常
    """
    pass


class Page:
    """
    页面类，包含一些基本页面识别方法
    """

    def __init__(self):
        self.pageName = None  # 页面名称
        self.dictPages = get_dictPages()  # 获取页面字典

    def reco_page(self):
        """
        识别当前页面
        :return: 页面名
        """
        img = screenshot()
        listTextModel = ocr_textAll(img)

        signLoop0 = True  # 外循环信号
        for modelPage in self.dictPages.values():
            if not signLoop0:  # 跳出外循环
                break

            signLoop1 = True  # 内循环信号
            for modelText in listTextModel:
                if not signLoop1:  # 跳出内循环
                    break

                if modelText.text == modelPage.text:  # 检测到页面特征文本
                    pageName = modelPage.pageName  # 标记当前页面名
                    pos = modelText.pos  # 标记页面特征位置
                    signLoop1 = False  # 跳出内循环
                    signLoop0 = False  # 跳出外循环

        try:
            modelPage = self.dictPages[pageName]  # 获取页面模型
            signRecordPos = get_signRecordPos(modelPage)  # 有无记录页面特征位置
            if signRecordPos:  # 需要记录页面特征位置
                self.dictPages[pageName].pos = pos  # 记录页面特征位置

                for modelPageRoute in modelPage.route:  # 循环记录次级页面特征位置
                    for modelText in listTextModel:
                        if modelText.text == modelPageRoute.text:  # 检测到次级页面特征文本
                            modelPageRoute.pos = modelText.pos  # 记录次级页面特征位置
                            break

                record_pageJson(self.dictPages[pageName])

            self.pageName = pageName  # 记录当前页面名
            return self.pageName

        except KeyError:
            raise UnknownPage("未知页面")

    def confirm_page(self, pageName: str):
        """
        通过关键字识别当前页面
        :param pageName: 页面名
        :return: 切换成功与否
        """
        model = self.dictPages[pageName]
        key = model.text
        img = screenshot()
        listTextModels = ocr_crop(img, model)
        if len(listTextModels) == 1:  # 确保只检测出一个结果
            if listTextModels[0].text == key:
                return True

            else:
                return False

        else:
            raise OCRResultError("OCR识别文本个数过多")

    def find_path(self, pageName: str):
        """
        寻路
        :param pageName: 目标界面名
        :return: 路径界面名列表
        """


class MainPage(Page):
    """
    主页类，用于任务模块界面的切换
    """

    def __init__(self):
        super().__init__()

    def change(self, pageName: str):
        """
        切换页面
        """
        self.reco_page()
        try:  # 如果页面存在该子页面
            textSpecial = dictPages[self.pageName].pageSon[pageName]
            control.click_text(textSpecial)
            while True:
                self.confirm_page(pageName)
                print(self.pageName)
                if self.pageName == pageName:
                    break

        except KeyError:  # 如果页面不存在该子页面
            print('当前页面不存在目标子页面')


class ShiBingYanXi(Page):
    """
    实兵演习界面
    """

    def check_battletimes(self):
        """
        检查战斗次数
        :return: 战斗次数
        """
        img = screenshot()  # 截图
        imgBattleTimes = crop_image(img, area=(3650, 60, 3740, 110))
        timesBattle = int(ocr_textAll(imgBattleTimes.image)[0][0][1][0])
        return timesBattle


if __name__ == "__main__":
    refresh_setting()
    pageMain = MainPage()
    print(pageMain.confirm_page("主界面"))
