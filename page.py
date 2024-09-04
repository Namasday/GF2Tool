import shutil

from PIL import Image

import json
import os
import subprocess
import time
from ctypes import windll

import cv2
import numpy as np
import win32con
import win32gui
import win32ui
from pydantic import BaseModel, Field

from constants import Setting
from control import Control
from utils import timer, ocr, logger, PositionModel

# 预设页面列表
listDictPages = [
    # 主界面
    {
        "pageName": "主界面",
        "modelSpecialText": {"text": "战役推进"},
        "route": [
            {
                "pageName": "剧情战役",
                "modelDirectText": {"text": "战役推进"}
            },
            {
                "pageName": "班组",
                "modelDirectText": {"text": "班组"}
            },
            {
                "pageName": "公共区",
                "modelDirectText": {"text": "公共区"},
            }
        ]
    },

    # 剧情战役分支
    {
        "pageName": "剧情战役",
        "modelSpecialText": {"text": "猎人评定"},
        "route": [
            {
                "pageName": "模拟作战",
                "modelDirectText": {"text": "模拟作战"}
            }
        ]
    },
    {
        "pageName": "模拟作战",
        "modelSpecialText": {"text": "心智勘测"},
        "route": [
            {
                "pageName": "实兵演习",
                "modelDirectText": {"text": "实兵演习"}
            }
        ]
    },
    {
        "pageName": "实兵演习",
        "modelSpecialText": {"text": "布设防御"},
        "route": []
    },

    # 班组分支
    {
        "pageName": "班组",
        "modelSpecialText": {"text": "要务"},
        "route": [
            {
                "pageName": "班组要务",
                "modelDirectText": {"text": "要务"}
            },
            {
                "pageName": "班组补给",
                "modelDirectText": {"text": "补给"}
            },
            {
                "pageName": "尘烟前线",
                "modelDirectText": {"text": "尘烟前线"}
            }
        ]
    },
    {
        "pageName": "班组要务",
        "modelSpecialText": {"text": "每日要务奖励"},
        "route": []
    },
    {
        "pageName": "班组补给",
        "modelSpecialText": {"text": "班组领取记录"},
        "route": []
    },
    {
        "pageName": "尘烟前线",
        "modelSpecialText": {"text": "班组表现"},
        "route": []
    },

    # 公共区分支
    {
        "pageName": "公共区",
        "modelSpecialText": {"text": "武器陈列室"},
        "route": [
            {
                "pageName": "休息室",
                "modelDirectText": {"text": "休息室"}
            },
            {
                "pageName": "调度室",
                "modelDirectText": {"text": "调度室"}
            }
        ]
    },
    {
        "pageName": "休息室",
        "modelSpecialText": {"text": "赠礼"},
        "route": []
    },
    {
        "pageName": "调度室",
        "modelSpecialText": {"text": "调度考核"},
        "route": [
            {
                "pageName": "情报储备",
                "modelDirectText": {"text": "调度收益"}
            }
        ]
    },
    {
        "pageName": "情报储备",
        "modelSpecialText": {"text": "情报储备情况"},
        "route": [
            {
                "pageName": "资源生产",
                "modelDirectText": {"text": "资源生产"}
            }
        ]
    },
    {
        "pageName": "资源生产",
        "modelSpecialText": {"text": "每小时产量"},
        "route": []
    },

    # 特殊
    {
        "pageName": "获得道具",
        "modelSpecialText": {"text": "点击空白处关闭"},
        "route": []
    },
    {
        "pageName": "加载",
        "modelSpecialText": {"text": "资源加载中"},
        "route": []
    },
    {
        "pageName": "作战准备",
        "modelSpecialText": {"text": "作战开始"},
        "route": []
    },
    {
        "pageName": "作战中",
        "modelSpecialText": {"text": "回合"},
        "route": []
    },
    {
        "pageName": "任务完成",
        "modelSpecialText": {"text": "指挥官等级"},
        "route": []
    },
    {
        "pageName": "伤害统计",
        "modelSpecialText": {"text": "伤害统计"},
        "route": []
    }
]


class TextModel(BaseModel):
    """
    文本模型
    """
    text: str = Field("", title="文本")
    pos: PositionModel = Field(None, title="文本位置模型")

    def __str__(self):
        return f"文本：{self.text}, 位置：{self.modelPos}"


class PageRouteModel(BaseModel):
    """
    页面转移路径模型
    """
    pageName: str = Field("", title="指向页面名称")
    modelDirectText: TextModel = Field(None, title="指向文本模型")

    def __str__(self):
        return f"下一界面名：{self.pageName}，指向文本：{self.text}"


class PageModel(BaseModel):
    """
    页面模型
    """
    pageName: str = Field("", title="页面名称")
    modelSpecialText: TextModel = Field(None, title="特征文本模型")
    route: list[PageRouteModel] = Field([], title="次级界面路径模型列表")

    def __str__(self):
        return f"页面名称：{self.pageName}，特征文本：{self.text}，下一界面路径列表：{self.route}"


def read_pageJson(dictPage):
    """
    读取页面json文件
    :return: 页面模型列表
    """
    try:  # 存在该页面json文件
        with open("json/page/" + dictPage['pageName'] + ".json", 'r', encoding='utf-8') as file:
            data = json.load(file)

        listDataRoute = []  # 预设路径文本列表
        for pageRoute in data['route']:
            listDataRoute.append(pageRoute['modelDirectText']['text'])

        listDictPagesRoute = []  # 默认路径文本列表
        for pageRoute in dictPage['route']:
            listDictPagesRoute.append(pageRoute['modelDirectText']['text'])

        if (
                data['modelSpecialText']['text'] == dictPage['modelSpecialText']['text'] and  # 特征文本与预设一致
                listDictPagesRoute == listDataRoute  # 下一界面路径与预设一致
        ):
            return data

        else:
            return dictPage

    except FileNotFoundError:  # 不存在该页面json文件
        return dictPage


def get_dictPages():
    """
    获取页面模型列表
    :return: 页面模型字典，字典键为页面名称，值为PageModel对象
    """
    _dictPages = {}  # 初始化全页面
    for dictPage in listDictPages:
        dictPage = read_pageJson(dictPage)  # 检索是否存在该页面json文件
        _dictPages[dictPage['pageName']] = PageModel(**dictPage)

    return _dictPages


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
    if not listResults:  # 检测不到文字报错
        return None

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


def textmatch_whole(text: str, modelText: TextModel) -> bool:
    """
    文字完整匹配
    :param text: 识别结果
    :param modelText: 文字模型
    :return: 匹配结果
    """
    if text == modelText.text:
        return True

    else:
        return False


def textmatch_part(text: str, modelText: TextModel) -> bool:
    """
    文字局部匹配
    :param text: 所求文字
    :param modelText: 文字模型
    :return: 匹配结果
    """
    if text in modelText.text:
        return True

    else:
        return False


def ocr_crop(image, modelText: TextModel):
    """
    裁剪图像识别文字
    :param image: 原图像，用以裁剪
    :param modelText: 文字模型
    :return: 识别结果
    """
    pos = modelText.pos
    imageCrop = image[pos.y1:pos.y2, pos.x1:pos.x2]
    listTextModel = ocr_textAll(imageCrop)
    if not listTextModel:  # 检测不到文字
        return None

    # 对识别结果的位置进行修正
    listReturnTextModel = []
    for modelText in listTextModel:
        text = modelText.text
        position = PositionModel(
            x1=modelText.pos.x1 + pos.x1,
            y1=modelText.pos.y1 + pos.y1,
            x2=modelText.pos.x2 + pos.x1,
            y2=modelText.pos.y2 + pos.y1
        )
        model = TextModel(
            text=text,
            pos=position
        )
        listReturnTextModel.append(model)

    return listReturnTextModel


def write_pageJson(modelPage):
    """
    将页面特征写入json文件
    """
    data = modelPage.dict()  # 获取页面特征json
    data = json.dumps(data, indent=4, ensure_ascii=False)  # 确保中文不会转义
    dirpath = 'json/page'
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    file = dirpath + '/' + modelPage.pageName + '.json'
    with open(file, 'w', encoding='utf-8') as file:
        file.write(data)   # 写入json文件


def get_signRecordPos(modelPage) -> bool:
    """
    决定是否记录页面特征
    :param modelPage: 页面模型
    :return: 是否记录页面特征位置
    """
    if not modelPage.modelSpecialText.pos:  # 页面特征位置未记录
        return True

    for modelPageRoute in modelPage.route:
        if not modelPageRoute.modelDirectText.pos:  # 次级页面特征位置未记录
            return True

    return False


class UnknownPage(Exception):
    """
    未知页面异常
    """
    pass


def delete_json():
    """
    启动时若检测到屏幕分辨率或缩放因子与预设不同，则删除page文件夹内的预设
    """
    path = 'json'
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        shutil.rmtree(file_path)


def start_game():
    """
    启动游戏
    """
    with open('config.json', 'r') as f:
        data = json.load(f)

    subprocess.Popen(data['gamepath'])


def get_scale_factor():
    """
    获取显示器的缩放系数
    :return: 缩放系数
    """
    try:
        windll.shcore.SetProcessDpiAwareness(1)  # 设置进程的 DPI 感知
        scale_factor = windll.shcore.GetScaleFactorForDevice(
            0
        )  # 获取主显示器的缩放因子
        return scale_factor / 100  # 返回百分比形式的缩放因子
    except Exception as e:
        print("Error:", e)
        return None


def write_imageJson(modelImage):
    """
    将图片模型写入json文件
    :param modelImage: 图片模型
    """
    data = modelImage.dict()  # 获取页面特征json
    data = json.dumps(data, indent=4, ensure_ascii=False)  # 确保中文不会转义
    dirpath = 'json/image'
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    file = dirpath + '/' + modelImage.text + '.json'
    with open(file, 'w', encoding='utf-8') as file:
        file.write(data)  # 写入json文件


def image_match(
        img: np.ndarray,
        imgTemplate: np.ndarray,
        area: PositionModel = PositionModel(
            x1=0,
            y1=0,
            x2=Setting.screenWidth,
            y2=Setting.screenHeight
        )
):
    """
    使用 opencv matchTemplate 方法在指定区域内进行模板匹配并返回匹配结果
    :param img:  大图片
    :param imgTemplate: 小图片
    :param area: 区域模型
    :return: ImgPosition 或 None
    """
    # 判断是否为灰度图，如果不是转换为灰度图
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if len(imgTemplate.shape) == 3:
        imgTemplate = cv2.cvtColor(imgTemplate, cv2.COLOR_BGR2GRAY)

    img = img[area.y1:area.y2, area.x1:area.x2]
    # 模板图片根据屏幕分辨率宽度进行缩放
    ratio = Setting.screenWidth / 3840
    imgTemplate = cv2.resize(imgTemplate, None, fx=ratio, fy=ratio, interpolation=cv2.INTER_AREA)

    # 模板匹配
    res = cv2.matchTemplate(img, imgTemplate, cv2.TM_CCOEFF_NORMED)
    confidence = np.max(res)
    if confidence < Setting.threshold:
        return None
    max_loc = np.where(res == confidence)

    return PositionModel(
        x1=area.x1 + max_loc[1][0],
        y1=area.y1 + max_loc[0][0],
        x2=area.x1 + max_loc[1][0] + imgTemplate.shape[1],
        y2=area.y1 + max_loc[0][0] + imgTemplate.shape[0],
    )


class Page:
    """
    页面类，包含一些基本页面识别方法
    """

    def __init__(self):
        # 声明
        self.limitRecoTimes = 5  # 识别次数限制
        self.limitRecoCD = 0.3  # 识别CD限制

        self.pageName = None  # 页面名称
        self.dictPages = get_dictPages()  # 获取页面字典
        self.route = []  # 路径界面名列表
        self.hwnd = None  # 窗口句柄
        self.boolWindowBar = None  # 窗口栏是否显示
        self.windowPosition = None  # 窗口位置
        self.scaleFactor = None  # 缩放系数

        self.__refresh_setting()  # 初始化设置
        self.control = Control(
            windowPosition=self.windowPosition
        )

    def get_resolution(self):
        """
        获取页面分辨率
        :param image: np图像
        :return:分辨率元组
        """
        img = self.screenshot()
        black_pixels_y = np.where(np.all(img[0] == 0, axis=1))[0]
        if black_pixels_y.size > 0:
            width = int(black_pixels_y[0])
        else:
            width = 3840

        black_pixels_x = np.where(np.all(img[:, 0] == 0, axis=1))[0]
        if black_pixels_x.size > 0:
            height = int(black_pixels_x[0])
        else:
            height = 2160

        return width, height

    def screenshot(self):
        """
        截图
        ：return: 截取到的图像np数组
        """
        hwndDC = win32gui.GetWindowDC(self.hwnd)  # 获取窗口设备上下文（DC）
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)  # 创建mfcDC
        saveDC = mfcDC.CreateCompatibleDC()  # 创建与mfcDC兼容的DC
        saveBitMap = win32ui.CreateBitmap()  # 创建一个位图对象
        saveBitMap.CreateCompatibleBitmap(mfcDC, Setting.screenWidth, Setting.screenHeight)  # 创建与mfcDC兼容的位图
        saveDC.SelectObject(saveBitMap)  # 选择saveDC的位图对象，准备绘图
        # 尝试使用PrintWindow函数截取窗口图像
        windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 3)

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
        win32gui.ReleaseDC(self.hwnd, hwndDC)

        return im  # 返回截取到的图像

    def __has_title_bar(self) -> bool:
        """
        判断窗口是否带有标题栏
        """
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_STYLE)
        return bool(style & win32con.WS_CAPTION)

    def get_window_position(self) -> tuple:
        """
        获取窗口位置
        :return: 窗口位置元组
        """
        rect = win32gui.GetWindowRect(self.hwnd)
        if self.boolWindowBar:  # 如果有标题栏
            pos = (rect[0], rect[1] + Setting.titleBarHeight)
        else:  # 如果没有标题栏
            pos = (rect[0], rect[1])
        return pos

    def __refresh_setting(self):
        """
        刷新设置
        :return: 检测窗口是否存在的布尔值
        """
        self.hwnd = win32gui.FindWindow("UnityWndClass", "少女前线2：追放")
        if not self.hwnd:
            logger("未找到游戏窗口，启动游戏")
            start_game()  # 启动游戏

        # 切换窗口至前台
        win32gui.SetForegroundWindow(self.hwnd)
        screenWidth, screenHeight = self.get_resolution()
        self.scaleFactor = get_scale_factor()
        if (
            Setting.screenWidth != screenWidth or
            Setting.screenHeight != screenHeight or
            Setting.scaleFactor != self.scaleFactor
        ):  # 如果界面分辨率和屏幕缩放因子与预设不同，则删除page文件夹内的预设重新获取
            Setting.screenWidth = screenWidth
            Setting.screenHeight = screenHeight
            Setting.scaleFactor = self.scaleFactor

            delete_json()  # 删除page文件夹内的预设

        self.boolWindowBar = self.__has_title_bar()  # 窗口是否有标题栏
        self.windowPosition = self.get_window_position()  # 获取窗口位置

    def reco_page(self, type: str = "whole"):
        """
        识别当前页面
        :return: 页面名
        """
        textmatch = None
        if type == "whole":  # 识别整个界面
            textmatch = textmatch_whole

        if type == "part":  # 识别部分界面
            textmatch = textmatch_part

        img = self.screenshot()
        listTextModel = ocr_textAll(img)

        signLoop0 = True  # 外循环信号
        pageName = None
        pos = None
        for modelPage in self.dictPages.values():
            if not signLoop0:  # 跳出外循环
                break

            signLoop1 = True  # 内循环信号
            for modelText in listTextModel:
                if not signLoop1:  # 跳出内循环
                    break

                if textmatch(
                    text=modelPage.modelSpecialText.text,
                    modelText=modelText
                ):  # 检测到页面特征文本
                    pageName = modelPage.pageName  # 标记当前页面名
                    pos = modelText.pos  # 标记页面特征位置
                    signLoop1 = False  # 跳出内循环
                    signLoop0 = False  # 跳出外循环

        try:
            modelPage = self.dictPages[pageName]  # 获取页面模型
            signRecordPos = get_signRecordPos(modelPage)  # 有无记录页面特征位置
            if signRecordPos:  # 需要记录页面特征位置
                self.dictPages[pageName].modelSpecialText.pos = pos  # 记录页面特征位置

                for modelPageRoute in modelPage.route:  # 循环记录次级页面特征位置
                    for modelText in listTextModel:
                        if modelText.text == modelPageRoute.modelDirectText.text:  # 检测到次级页面特征文本
                            modelPageRoute.modelDirectText.pos = modelText.pos  # 记录次级页面特征位置
                            break

                write_pageJson(self.dictPages[pageName])

            self.pageName = pageName  # 记录当前页面名
            return self.pageName

        except KeyError:
            return "未知界面"

    def confirm_page(self, pageName: str) -> bool:
        """
        通过关键字识别当前页面
        :param pageName: 页面名
        :return: 切换成功与否
        """
        model = self.dictPages[pageName]
        signRecordPos = get_signRecordPos(model)
        if signRecordPos:  # 目标页面特征位置需要记录
            pageNameReco = self.reco_page()
            if pageNameReco == pageName:
                return True
            else:
                return False

        else:
            key = model.modelSpecialText.text
            img = self.screenshot()
            listTextModels = ocr_crop(img, model.modelSpecialText)
            if not listTextModels:  # 未识别出文本
                return False

            if len(listTextModels) == 1:  # 确保只检测出一个结果
                if listTextModels[0].text == key:
                    self.pageName = pageName
                    return True

                else:
                    return False

            else:
                raise OCRResultError("OCR识别文本个数过多")

    def __find_path_loop(self, pageName: str):
        """
        寻路循环体
        :param pageName: 目标界面名
        :return: 路径界面名列表
        """
        check = False  # 查找是否有所求页面
        for modelPage in self.dictPages.values():
            if modelPage.pageName == pageName:
                self.route.append(pageName)
                check = True
                break

        if check:
            signLoop0 = True  # 外循环信号
            for modelPage in self.dictPages.values():
                if not signLoop0:  # 跳出外循环
                    break

                signLoop1 = True  # 内循环信号
                for modelPageRoute in modelPage.route:
                    if not signLoop1:  # 跳出内循环
                        break

                    if modelPageRoute.pageName == pageName:
                        self.__find_path_loop(modelPage.pageName)
                        signLoop1 = False  # 跳出内循环
                        signLoop0 = False  # 跳出外循环

    def find_path(self, pageName: str):
        """
        寻路并重置路径
        :param pageName: 目标界面名
        :return: 路径界面名列表
        """
        self.__find_path_loop(pageName)
        route = self.route

        if len(route) == 0:  # 路径长度为0
            raise UnknownPage(f"无法到达页面：{pageName}，请检查listDictPages预设")

        else:
            self.route = []
            route.reverse()  # 路径列表反转
            return route

    def reco_image(self, imageName):
        """
        :param imageName: 模板图片名
        :return: 图片模型，包含图片名和位置模型
        """
        fileName = imageName + ".json"
        if fileName in os.listdir("json/"):  # 如果已有模板图片预设文件则读取
            with open("json/" + fileName, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return data

        img = self.screenshot()
        imageTemplate = cv2.imread(Setting.dictTemplatePath[imageName], 0)
        pos = image_match(img, imageTemplate)
        if pos:
            model = TextModel(text=imageName, pos=pos)
            write_imageJson(model)
            return model

        else:
            return None

    def click_image(self, imageName: str):
        """
        点击图片
        :param imageName: 模板图片名，查询Setting.dictTemplatePath
        :return: 点击成功与否
        """
        model = self.reco_image(imageName)
        if model:
            self.control.random_click(model.pos)
            return True

        else:
            return False

    def retrun_to_mainPage(self):
        """
        返回主页
        """
        listTemplateName = ["返回主界面_黑", "返回主界面_白"]
        for imageName in listTemplateName:
            sign = self.click_image(imageName)
            if sign:
                return

        raise UnknownPage("无法返回主界面")

    def confirm_loop(self, pageName: str, timeWait: float = 0):
        """
        循环确认界面
        :param pageName: 目标界面名
        :param timeWait: 等待动画时间
        :return: 确认成功与否
        """
        time.sleep(timeWait)
        for _ in range(self.limitRecoTimes):
            if self.confirm_page(pageName):
                return True  # 确认成功

            time.sleep(self.limitRecoCD)

        return False  # 确认失败

    def change(self, pageNow: str, pageNext):
        """
        切换界面
        :param pageNow: 当前界面名
        :param pageNext: 下一个界面名

        """
        modelPage = self.dictPages[pageNow]
        pos = None  # 下一界面指向文本位置模型

        # 寻找指向文本位置
        for modelPageRoute in modelPage.route:
            if pageNext == modelPageRoute.pageName:
                pos = modelPageRoute.modelDirectText.pos
                break

        # 由于战役推进可能会指向3个界面，所以设立此项
        listSpecialPage = ['剧情战役', '模拟作战']

        # 切换界面
        while True:  # 仍处于当前界面
            if self.confirm_page(pageNow):  # 确认界面
                self.control.random_click(pos)
                time.sleep(self.limitRecoCD)

            if self.confirm_page(pageNext):  # 确认界面
                return
            elif pageNext in listSpecialPage:  # 特殊界面
                for pageName in listSpecialPage:  # 特殊界面
                    if self.confirm_page(pageName):  # 确认界面
                        return

    def locate(self, pageName: str):
        """
        导航至目标界面
        :param pageName:
        :return:
        """
        route = self.find_path(pageName)  # 寻路
        self.reco_page()  # 识别当前界面

        if self.pageName in route:  # 当前界面是否在寻路路径中
            route = route[route.index(self.pageName):]  # 从当前界面开始截取寻路路径

        else:  # 不在寻路路径中，返回主界面
            self.retrun_to_mainPage()
            signConfirm = self.confirm_loop('主界面')
            if not signConfirm:
                return self.locate(pageName)

        # 切换界面
        for index, routePageName in enumerate(route):
            if index + 1 >= len(route):  # 判断是否为最后一个界面
                break

            self.change(route[index], route[index + 1])

    def wait_page(self, pageName: str):
        """
        无限循环等待目标界面出现
        :param pageName:
        """
        while True:
            if self.confirm_page(pageName):  # 确认界面
                return

            time.sleep(1)


class TaskPage(Page):
    def __init__(self, taskName):
        super().__init__()
        self.taskName = taskName
        self.listTextModel = []  # 文本模型列表
        self.dictText = self.read_taskJson()

    def read_taskJson(self):
        """
        读取任务界面json文件
        """
        dictText = {}
        try:
            with open("json/task/" + self.taskName + ".json", 'r', encoding='utf-8') as file:
                listTextModel = json.load(file)

            for modelText in listTextModel:
                modelText = TextModel(**modelText)
                dictText[modelText.text] = modelText.pos

        except FileNotFoundError:
            pass

        finally:
            return dictText

    def write_taskJson(self):
        """
        写入任务界面json文件
        """
        # 将列表里的文本模型解成字典并传入jsonTextModels列表
        jsonTextModels = []
        for modelText in self.listTextModel:
            data = modelText.dict()
            jsonTextModels.append(data)

        dirpath = 'json/task'
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        file = os.path.join(dirpath, self.taskName + '.json')
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(jsonTextModels, f, indent=4, ensure_ascii=False)  # 写入json文件

    def click_text(self, text: str) -> bool:
        """
        点击文本
        :param text: 目标文本
        """
        img = self.screenshot()
        listTextModel = []
        try:
            pos = self.dictText[text]
            model = TextModel(text=text, pos=pos)
            listTextModel = ocr_crop(img, model)

        except KeyError:
            img = self.screenshot()
            listTextModel = ocr_textAll(img)

            for modelText in listTextModel:
                if textmatch_whole(text, modelText):
                    self.dictText[modelText.text] = modelText.pos
                    self.listTextModel.append(modelText)
                    break

            self.write_taskJson()

        finally:
            if not listTextModel:
                logger(f"未找到文本：{text}")
                return False

            elif len(listTextModel) == 1 and listTextModel[0].text == text:
                self.control.random_click(listTextModel[0].pos)
                return True

    def auto_battle(self):
        """
        自动战斗
        """
        templateName = "自动战斗"
        self.click_image(templateName)

    def battle(self):
        """
        战斗
        """
        self.wait_page('作战准备')
        model = self.dictPages['作战准备']
        self.control.random_click(model.modelSpecialText.pos)

        self.wait_page('作战中')
        self.auto_battle()

        self.wait_page('任务完成')
        self.control.click_blank()

        self.wait_page('伤害统计')
        self.click_text('确认')


listTask = []


def init_task(cls):
    listTask.append(cls)
    return cls


class BanZuBuji(TaskPage):
    def __init__(self):
        self.taskName = '班组补给'
        super().__init__(self.taskName)

    def run(self):
        """
        收获
        :return:
        """
        self.locate('班组补给')
        sign = self.click_text('领取全部')
        if not sign:  # 未找到领取全部
            return

        sign = self.confirm_loop('获得道具')
        if sign:
            self.control.click_blank()


class PaiQian(TaskPage):
    def __init__(self):
        self.taskName = '派遣'
        super().__init__(self.taskName)

    def run(self):
        self.locate('调度室')
        sign = self.click_text('一键领取')
        if not sign:  # 未找到一键领取
            return

        sign = self.click_text('再次派遣')
        if sign:
            time.sleep(2)


class QingBaoCuBei(TaskPage):
    def __init__(self):
        self.taskName = '情报储备'
        super().__init__(self.taskName)


    def run(self):
        self.locate('情报储备')
        time.sleep(1)
        self.click_text('最大')
        time.sleep(1)
        sign = self.click_text('取出')
        if sign:
            time.sleep(2)


@init_task
class ZiYuanShengChan(TaskPage):
    """
    资源生产done
    """
    def __init__(self):
        self.taskName = '资源生产'
        super().__init__(self.taskName)

    def run(self):
        self.locate('资源生产')
        self.click_text('收取')

        sign = self.confirm_loop('获得道具')
        if sign:
            self.control.click_blank()
            time.sleep(1)


class BanZuYaoWu(TaskPage):
    def __init__(self):
        self.taskName = '班组要务'
        super().__init__(self.taskName)

    def close(self):
        templateName = "关闭要务"
        self.click_image(templateName)
        self.wait_page('班组')  # 等待关闭动画结束

    def run(self):
        self.locate('班组要务')
        sign = self.click_text('开始作战')
        if not sign:
            logger(f"{self.taskName} 已完成")
            self.close()
            return

        self.battle()

        self.wait_page('班组要务')
        self.close()

class ShiBingYanXi(TaskPage):
    def __init__(self):
        self.taskName = '班组要务'
        super().__init__(self.taskName)

    def run(self):
        self.locate('班组要务')


if __name__ == "__main__":
    page = BanZuYaoWu()
    page.run()
