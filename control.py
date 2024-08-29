import time

import cv2
import numpy as np
import win32api
import win32con

from constants import Setting
from utils import screenshot, ocr, TargetPosition, calculate_boxCenter, image_match


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

    def click_text(self, text: str):
        """
        点击文字区域
        :param text: 目标文字
        """
        # 截图
        img = screenshot()

        # 文字识别
        listResults = ocr(img)[0]

        # 遍历所有识别结果寻找目标文字
        for result in listResults:
            if text == result[1]:  # 找到目标文字
                box = result[0]
                confidence = result[2]
                if confidence > Setting.threshold:
                    box = TargetPosition(
                        x1=box[0][0],
                        y1=box[0][1],
                        x2=box[2][0],
                        y2=box[2][1],
                        confidence=confidence,
                    )

                    center = calculate_boxCenter(box)
                    self.random_click(center[0], center[1], range_x=center[0]-box.x1, range_y=center[1]-box.y1)
                    return True

        return False

    def click_home(self):
        """
        点击主页按钮
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


control = Control()
