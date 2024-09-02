import random
import time

import win32api
import win32con

from constants import Setting
from utils import PositionModel


class Control:
    def __init__(self, windowPosition):
        self.windowPosition = windowPosition

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
        pos模型区域内随机点击
        :param pos: 目标框
        """
        random_x = random.randint(pos.x1, pos.x2)
        random_y = random.randint(pos.y1, pos.y2)
        self.click(random_x, random_y)

    def click_blank(self):
        """
        点击空白处
        """
        pos = PositionModel(
            x1=Setting.screenWidth / 4,
            y1=Setting.screenHeight / 5 * 4,
            x2=Setting.screenWidth / 4 * 3,
            y2=Setting.screenHeight,
        )
        self.random_click(pos)

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
