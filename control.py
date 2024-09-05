import random
import time

import win32api
import win32con

from constants import Setting
from utils import PositionModel


class Control:
    def __init__(self, windowPosition):
        self.windowPosition = windowPosition

    def click(self, x: int = 0, y: int = 0):
        x = x + self.windowPosition[0]
        y = y + self.windowPosition[1]
        win32api.SetCursorPos((x, y))
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

    def random_click(self, pos: PositionModel):
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

    def mouse_reset(self, x: int = None, y: int = None):
        x = int(Setting.screenWidth / 2) if not x else x
        y = int(Setting.screenHeight / 2) if not y else y
        x = x + self.windowPosition[0]
        y = y + self.windowPosition[1]
        win32api.SetCursorPos((x, y))

    def mouse_clickdown(self, x: int = 0, y: int = 0):
        x = x + self.windowPosition[0]
        y = y + self.windowPosition[1]
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)

    def mouse_clickup(self, x: int = 0, y: int = 0):
        x = x + self.windowPosition[0]
        y = y + self.windowPosition[1]
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

    def mouse_move(self, x: int = 0, y: int = 0, offset=(0, 0), duration: float = 0.01):
        # 计算移动的总距离和步数
        dx = offset[0]
        dy = offset[1]
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            steps = 1  # 防止除以零

        # 每一步移动的距离
        step_dx = dx / steps
        step_dy = dy / steps

        self.mouse_reset(x, y)
        self.mouse_clickdown(x, y)

        for _ in range(int(steps)):
            x = x + int(round(step_dx * (_ + 1)))
            y = y + int(round(step_dy * (_ + 1)))
            win32api.SetCursorPos((x + self.windowPosition[0], y + self.windowPosition[1]))
            time.sleep(duration / steps)  # 简单的延时来模拟拖动速度

        # 释放鼠标按钮
        self.mouse_clickup(x + dx, y + dy)
