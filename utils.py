from ctypes import windll
import cv2
import numpy as np
import win32con
import win32gui
import win32ui
from pydantic import BaseModel, Field
from constants import Setting

from rapidocr_openvino import RapidOCR

from control import control

ocr = RapidOCR()


def locate(
    route: list,
    dictRoute: dict,
):
    """
    导航至目标界面
    :param route: 路线界面列表
    :param dictRoute: 路线字典
    """
    pageNow = reco_page()
    if pageNow in route:
        if pageNow == route[-1]:
            return

        index = route.index(pageNow)
        route = route[index:]
    else:
        done = control.click_home()
        if not done:
            logger("未知界面，无法返回主界面")
            return

    for page in route[:-1]:
        while True:
            done = control.click_text(dictRoute[page])
            if done:
                break


def logger(text):
    print(text)


def reco_page():
    """
    识别当前界面
    :return: 界面名
    """
    # 截图
    img = screenshot()

    listResults = ocr(img)[0]
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


def has_title_bar():
    # 获取窗口的样式
    # 注意：对于32位Python或旧版本的pywin32，可能需要使用GetWindowLong而不是GetWindowLongPtr
    style = win32gui.GetWindowLong(Setting.hwnd, win32con.GWL_STYLE)

    # 检查样式中是否包含WS_CAPTION
    # 如果包含，则认为有标题栏
    return bool(style & win32con.WS_CAPTION)


def get_window_position():
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


def calculate_boxCenter(box: TargetPosition):
    x = (box.x1 + box.x2) / 2
    y = (box.y1 + box.y2) / 2
    return int(x), int(y)


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

    Setting.screenWidth, Setting.screenHeight = get_resolution(screenshot())
    Setting.scaleFactor = get_scale_factor()  # 获取缩放比例
    Setting.windowBar = has_title_bar()  # 窗口是否有标题栏
    Setting.windowPosition = get_window_position()  # 获取窗口位置
    return True
