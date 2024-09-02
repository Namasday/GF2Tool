import random
import time

import numpy as np
import win32api
import win32con

from constants import Setting
from page import PositionModel


class Control:
    def __init__(self, **kwargs):
        self.windowPosition = kwargs['windowPosition']

    def click(self, x=0, y=0):
        x = x if isinstance(x, int) else int(x)
        y = y if isinstance(y, int) else int(y)
        x = x + self.windowPosition[0]
        y = y + self.windowPosition[1]
        win32api.SetCursorPos((x, y))
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

    def random_click(
            self,
            pos: PositionModel
    ):
        """
        在以 (x, y) 为中心的区域内随机选择一个点并模拟点击。
        :param pos: 目标框
        """
        random_x = random.randint(pos.x1, pos.x2)
        random_y = random.randint(pos.y1, pos.y2)
        self.click(random_x, random_y)
        logger.info(f'点击位置: ({random_x}, {random_y})')

    def click_box(self, box: PositionModel):
        """
        点击目标框
        :param box: 目标框
        """

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
