import json
import os
import subprocess
import time
from ctypes import windll
from dataclasses import dataclass

import cv2
import numpy as np
import win32api
import win32con
import win32gui
import win32ui
from pydantic import BaseModel, Field
from constants import Setting

from rapidocr_openvino import RapidOCR
ocr = RapidOCR(
    min_height=210,
    det_limit_side_len=40,
)

@dataclass
class CropImage:
    image: np.ndarray = None
    position: tuple = (0, 0)



def timer(func):
    """
    一个装饰器，用于计算并打印函数的执行时间
    """
    def wrapper(*args, **kwargs):
        # 记录开始时间
        start_time = time.time()
        # 调用原函数
        result = func(*args, **kwargs)
        # 记录结束时间
        end_time = time.time()
        # 计算并打印执行时间
        print(f"{func.__name__} executed in {end_time - start_time:.8f} seconds")
        # 返回原函数的返回值
        return result
    return wrapper


def crop_image(
    image: np.ndarray,
    area: tuple = None,
    ratio: tuple = None
):
    """
    对图片裁剪，返回图片模型
    :param image: 原图像
    :param area: 像素坐标裁剪，元组格式(x1, y1, x2, y2)
    :param ratio: 比例坐标裁剪，元组格式(x1, y1, x2, y2)
    :return: 裁剪后的图像ImageModel
    """
    # 初始化box
    x1, y1, x2, y2 = (0, 0, 0, 0)

    if area:  # 如果是像素坐标裁剪
        rate = Setting.screenWidth / 3840
        x1 = int(area[0] * rate)
        y1 = int(area[1] * rate)
        x2 = int(area[2] * rate)
        y2 = int(area[3] * rate)

    elif ratio:  # 如果是比例裁剪
        x1 = int(Setting.screenWidth * ratio[0])
        y1 = int(Setting.screenWidth * ratio[1])
        x2 = int(Setting.screenWidth * ratio[2])
        y2 = int(Setting.screenWidth * ratio[3])

    img = image[y1:y2, x1:x2]
    return CropImage(image=img, position=(x1, y1))


def confirm_click(timeout=30):
    """
    装饰器：循环运行函数直到它返回True或达到最大重试次数。
    :param timeout: 最大重试时间，默认为60秒。
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            now = time.time()
            while time.time() - now < timeout:
                result = func(*args, **kwargs)
                if result:
                    return result
            # 所有重试都失败了
            return logger("操作超时")

        return wrapper

    return decorator


def locate(text: str):
    """
    导航至目标界面
    :param text: 目标界面名
    """
    listPage = Setting.dictLocate[text]['listPage']
    dictRoute = Setting.dictLocate[text]['dictRoute']
    pageNow = reco_page()
    if pageNow in listPage:
        if pageNow == listPage[-1]:
            return

        index = listPage.index(pageNow)
        listPage = listPage[index:]
    else:
        done = control.click_home()
        if not done:
            logger("未知界面，无法返回主界面")
            return

    for page in listPage[:-1]:
        # 步进界面
        control.click_text(dictRoute[page])


def logger(text):
    print(text)


# @confirm_recopage()
def reco_page():
    """
    识别当前界面
    :return: 界面名
    """
    # 截图
    img = screenshot()

    # 文字识别
    listResults = ocr(img)[0]

    # 判断界面有无文本
    if not listResults:
        return "无文本界面"

    listResultsTexts = []
    for result in listResults:
        listResultsTexts.append(result[1])

    for key, value in Setting.textdictReco.items():
        if value in listResultsTexts:  # 检测到特征文本
            return key

    return "未知界面"


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


def has_title_bar() -> bool:
    """
    判断窗口是否带有标题栏
    """
    style = win32gui.GetWindowLong(Setting.hwnd, win32con.GWL_STYLE)
    return bool(style & win32con.WS_CAPTION)


def get_window_position() -> tuple:
    """
    获取窗口位置
    :return: 窗口位置元组
    """
    rect = win32gui.GetWindowRect(Setting.hwnd)
    if Setting.windowBar:  # 如果有标题栏
        pos = (rect[0], rect[1] + Setting.titleBarHeight)
    else:  # 如果没有标题栏
        pos = (rect[0], rect[1])
    return pos


def get_resolution(image):
    """
    获取图像的分辨率
    :param image: np图像
    :return:分辨率元组
    """
    black_pixels_y = np.where(np.all(image[0] == 0, axis=1))[0]
    if black_pixels_y.size > 0:
        width = int(black_pixels_y[0])
    else:
        width = 3840

    black_pixels_x = np.where(np.all(image[:, 0] == 0, axis=1))[0]
    if black_pixels_x.size > 0:
        height = int(black_pixels_x[0])
    else:
        height = 2160

    return width, height


def screenshot():
    """
    截取当前窗口的屏幕图像。
    通过调用Windows图形设备接口（GDI）和Python的win32gui、win32ui模块，
    本函数截取指定窗口的图像，并将其存储为numpy数组。
    ：param hwnd: 窗口句柄
    ：return: 截取到的图像
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


class Position(BaseModel):
    x1: int = Field(None, title="x1")
    y1: int = Field(None, title="y1")
    x2: int = Field(None, title="x2")
    y2: int = Field(None, title="y2")

    def __call__(self):
        return (self.x1, self.y1), (self.x2, self.y2)

    def __str__(self):
        return f"({self.x1}, {self.y1}, {self.x2}, {self.y2})"

    def __repr__(self):
        return f"({self.x1}, {self.y1}, {self.x2}, {self.y2})"


class TargetPosition(Position):
    confidence: float = Field(0, title="识别置信度")


class SpecialPositionJson(Position):
    textSpecial: str = Field(None, title="特征文本")


def image_match(
        img: np.ndarray,
        imgTemplate: np.ndarray,
        region: tuple = None,
        threshold: float = 0.8,
):
    """
    使用 opencv matchTemplate 方法在指定区域内进行模板匹配并返回匹配结果
    :param img:  大图片
    :param imgTemplate: 小图片
    :param region: 区域（x1, y1, x2, y2），默认为 None 表示全图搜索
    :param threshold:  阈值
    :return: ImgPosition 或 None
    """
    # 判断是否为灰度图，如果不是转换为灰度图
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if len(imgTemplate.shape) == 3:
        imgTemplate = cv2.cvtColor(imgTemplate, cv2.COLOR_BGR2GRAY)
    # 如果提供了region参数，则裁剪出指定区域，否则使用整幅图像
    if region:
        x1, y1, x2, y2 = region
        cropped_img = img[y1:y2, x1:x2]
    else:
        cropped_img = img
        x1, y1 = 0, 0

    ratio = Setting.screenWidth / 3840
    imgTemplate = cv2.resize(imgTemplate, None, fx=ratio, fy=ratio, interpolation=cv2.INTER_AREA)
    res = cv2.matchTemplate(cropped_img, imgTemplate, cv2.TM_CCOEFF_NORMED)
    confidence = np.max(res)
    if confidence < threshold:
        return None
    max_loc = np.where(res == confidence)

    return TargetPosition(
        x1=max_loc[1][0] + x1,
        y1=max_loc[0][0] + y1,
        x2=max_loc[1][0] + x1 + imgTemplate.shape[1],
        y2=max_loc[0][0] + y1 + imgTemplate.shape[0],
        confidence=confidence,
    )


def text_match(text: str):
    img = screenshot()
    listResults = ocr(img)[0]

    if not listResults:
        return text_match(text)
    for result in listResults:
        if text == result[1]:
            box = result[0]
            confidence = result[2]
            if confidence > Setting.threshold:
                return TargetPosition(
                    x1=box[0][0],
                    y1=box[0][1],
                    x2=box[2][0],
                    y2=box[2][1],
                    confidence=confidence,
                )

    return None


def textcrop_match(text: str):
    img = screenshot()
    listResults = ocr(img)[0]

    if not listResults:
        return text_match(text)
    for result in listResults:
        if text in result[1]:
            box = result[0]
            confidence = result[2]
            if confidence > Setting.threshold:
                return TargetPosition(
                    x1=box[0][0],
                    y1=box[0][1],
                    x2=box[2][0],
                    y2=box[2][1],
                    confidence=confidence,
                )

    return None


def reco_image(text: str):
    """
    检测画面是否存在模板图片
    :return:
    """
    # 截图
    img = screenshot()

    # 导入主页模板图片并创建列表
    template = cv2.imread(Setting.dictTemplate[text], 0)

    # 转换为cv2图像
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    return image_match(img, template)  # 使用模板匹配


def ocr_roi(region: tuple):
    """
    使用ocr识别特定区域文字
    :param region: 裁切区域
    :return: 目标字符串字典
    """
    img = screenshot()
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 裁剪
    x1, y1, x2, y2 = region
    cropped_img = img[y1:y2, x1:x2]

    listResults = ocr(cropped_img)[0]
    dictResults = {}
    for result in listResults:
        text = result[1]
        box = result[0]
        confidence = result[2]

        # 创建实例
        dictResults[text] = TargetPosition(
            x1=box[0][0] + x1,
            y1=box[0][1] + y1,
            x2=box[2][0] + x1,
            y2=box[2][1] + y1,
            confidence=confidence,
        )

    return dictResults


def calculate_boxCenter(box: TargetPosition):
    x = (box.x1 + box.x2) / 2
    y = (box.y1 + box.y2) / 2
    return int(x), int(y)


class Control:
    def click(self, x=0, y=0):
        x = x if isinstance(x, int) else int(x)
        y = y if isinstance(y, int) else int(y)
        x = x + Setting.windowPosition[0]
        y = y + Setting.windowPosition[1]
        win32api.SetCursorPos((x, y))
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

    def random_click(
            self,
            x: int = None,
            y: int = None,
            range_x: int = 3,
            range_y: int = 3,
            ratio: bool = False,
            need_print: bool = False,
    ):
        """
        在以 (x, y) 为中心的区域内随机选择一个点并模拟点击。

        :param x: 中心点的 x 坐标
        :param y: 中心点的 y 坐标
        :param range_x: 水平方向随机偏移的范围
        :param range_y: 垂直方向随机偏移的范围
        :param ratio: 是否将坐标进行缩放
        :param need_print: 是否输出log，debug用
        """
        random_x = x + np.random.uniform(-range_x, range_x)
        random_y = y + np.random.uniform(-range_y, range_y)

        # 将浮点数坐标转换为整数像素坐标
        if ratio:
            # 需要缩放
            random_x = int(random_x * Setting.scaleFactor)
            random_y = int(random_y * Setting.scaleFactor)
        else:
            # 不需要缩放
            random_x = int(random_x)
            random_y = int(random_y)

        # 点击
        time.sleep(np.random.uniform(0, 0.1))  # 随机等待后点击
        self.click(random_x, random_y)

    def click_box(self, box: TargetPosition):
        """
        点击目标框
        :param box: 目标框
        """
        center = calculate_boxCenter(box)
        self.random_click(
            center[0],
            center[1],
            range_x=center[0] - box.x1,
            range_y=center[1] - box.y1
        )

    @confirm_click()
    def click_text(self, text: str):
        """
        点击文字区域
        :param text: 目标文字
        :return: 点击成功与否的布尔值
        """
        box = text_match(text)
        if box:
            self.click_box(box)
            return True
        else:
            return False

    @confirm_click()
    def click_home(self):
        """
        点击主页按钮
        :return: 点击成功与否的布尔值
        """
        # 截图
        img = screenshot()

        # 导入主页模板图片并创建列表
        templateBlack = cv2.imread('template/mainpage_black.png', 0)
        templateWhite = cv2.imread('template/mainpage_white.png', 0)
        listTemplate = [templateWhite, templateBlack]

        # 转换为cv2图像
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        detected = False  # 判断是否找到
        position = None  # 记录位置
        for template in listTemplate:
            position = image_match(img, template)  # 使用模板匹配

            if position:
                detected = True
                break

        if detected:
            center = calculate_boxCenter(position)
            control.random_click(center[0], center[1])
            return True
        else:
            return False

    @confirm_click()
    def click_space(self):
        """
        带识别文字的点击空白处
        :return: 点击成功与否的布尔值
        """
        img = screenshot()
        listResults = ocr(img)[0]
        for result in listResults:
            if result[1] == "点击空白处关闭":
                self.click_blank()
                return True

        return False

    def click_blank(self):
        """
        点击空白处
        """
        self.random_click(
            Setting.screenWidth / 2,
            Setting.screenHeight / 10 * 9,
            range_x=Setting.screenWidth / 4,
            range_y=Setting.screenHeight / 10
        )

    @confirm_click()
    def click_image(self, text: str):
        """
        点击图片区域
        :param text: 图片名
        :return: 点击成功与否的布尔值
        """
        # 截图
        img = screenshot()

        # 导入主页模板图片并创建列表
        template = cv2.imread(Setting.dictTemplate[text], 0)

        # 转换为cv2图像
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        position = image_match(img, template)  # 使用模板匹配

        if position:
            center = calculate_boxCenter(position)
            control.random_click(center[0], center[1])
            return True
        else:
            return False


control = Control()


def battle():
    """
    战斗函数
    """
    boolAutoBattle = False  # 自动战斗状态
    boolBattle = False  # 战斗状态
    now = time.time()
    while True:
        if time.time() - now > 60:  # 60秒后超时
            return "作战超时"

        pageNow = reco_page()

        if pageNow in "加载":
            time.sleep(1)
            now = time.time()

        elif pageNow == "未知界面":
            if boolBattle and not boolAutoBattle:  # 战斗开始但未进入自动战斗
                box = reco_image("自动战斗")
                if box:
                    control.click_box(box)
                    boolAutoBattle = True
                    now = time.time()

            elif boolBattle and boolAutoBattle:  # 自动战斗中
                time.sleep(1)
                now = time.time()

        elif pageNow == "作战准备":
            control.click_text("作战开始")
            boolBattle = True
            now = time.time()

        elif pageNow == "晋升":
            control.click_blank()
            time.sleep(2)

        elif pageNow == "伤害统计":
            control.click_text("确认")

            # 战斗结束等待返回UI界面
            time.sleep(5)
            return "战斗结束"

        elif pageNow == "任务完成":
            boolBattle = False
            control.click_blank()
            time.sleep(2)


def login():
    while True:
        pageNow = reco_page()
        print(pageNow)
        if pageNow == "主界面":
            return "登录成功"

        if pageNow in ["登录", "收获"]:
            control.click_blank()
            time.sleep(1)
            continue

        if pageNow in ["加载", "未知界面", "无文本界面"]:
            time.sleep(1)
            continue


def delete_pagejson():
    """
    启动时若检测到屏幕分辨率或缩放因子与预设不同，则删除page文件夹内的预设
    """
    path = 'page'

    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        os.remove(file_path)


def start_game():
    """
    启动游戏
    """
    with open('config.json', 'r') as f:
        data = json.load(f)

    subprocess.Popen(data['gamepath'])


def refresh_setting():
    """
    刷新设置
    :return: 检测窗口是否存在的布尔值
    """
    Setting.hwnd = win32gui.FindWindow("UnityWndClass", "少女前线2：追放")
    if not Setting.hwnd:
        return False

    # 切换窗口至前台
    win32gui.SetForegroundWindow(Setting.hwnd)

    screenWidth, screenHeight = get_resolution(screenshot())
    scaleFactor = get_scale_factor()  # 获取缩放比例
    if (
            Setting.screenWidth != screenWidth or
            Setting.screenHeight != screenHeight or
            Setting.scaleFactor != scaleFactor
    ):  # 如果界面分辨率和屏幕缩放因子与预设不同，则删除page文件夹内的预设重新获取
        Setting.screenWidth = screenWidth
        Setting.screenHeight = screenHeight
        Setting.scaleFactor = get_scale_factor()

        delete_pagejson()  # 删除page文件夹内的预设

    Setting.windowBar = has_title_bar()  # 窗口是否有标题栏
    Setting.windowPosition = get_window_position()  # 获取窗口位置
    return True


if __name__ == '__main__':
    running = refresh_setting()
    print(reco_page())