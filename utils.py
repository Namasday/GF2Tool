import json
import subprocess
import time
from dataclasses import dataclass

import cv2
import numpy as np
from pydantic import BaseModel, Field

from constants import Setting

from rapidocr_openvino import RapidOCR
ocr = RapidOCR(
    min_height=210,
    det_limit_side_len=40,
)


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


def logger(text):
    print(text)


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
