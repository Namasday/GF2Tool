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


def logger(text):
    print(text)


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
