import time

from constants import Setting
from page import ShiBingYanXi
from utils import locate, control, text_match, battle

class Task:
    def done(self, time=5):
        """
        任务完成，等待时间响应
        :param time: 等待时间
        """
        time.sleep(time)

    def banzu_yaowu(self):
        """
        战斗：要务done
        """
        locate("班组要务")
        time.sleep(1)
        box = text_match("开始作战")
        if box:
            control.click_box(box)
            battle()

        while True:
            box = text_match("每日要务已完成")
            if box:
                control.click_blank()
                break

    def banzu_buji(self):
        """
        收获：补给done
        """
        locate("班组补给")
        time.sleep(2)
        box = text_match("领取全部")
        if box:
            control.click_box(box)
            control.click_space()

    def shibingyanxi(self):
        """
        战斗：实兵演习
        """
        locate("实兵演习")
        instance = ShiBingYanXi()

        timesBattle = instance.check_battletimes()
        if timesBattle == 3 - Setting.timeslimitBattle:  # 战斗次数为0，
            return

        # control.click_text("进攻")
        # ratio = Setting.screenWidth / 3840
        # area = [490, 1180, 3090, 1250]
        # timesBattle = 3  # 每日次数
        # timesRefresh = 5  # 刷新次数
        # roi = [int(num/ratio) for num in area]
        # time.sleep(2)

        # while timesBattle > 0:
        #     dictResults = ocr_roi(region=tuple(roi))
        #     listNum = [int(num) for num in dictResults.keys()]
        #     listFightingCapacity = [num for num in listNum if num < Setting.fightingCapacity]
        #     count = len(listFightingCapacity)  # 判断是否有战力低于阈值的玩家
        #     if count > 0:
        #         for num in listFightingCapacity:
        #             num = str(num)  # 转换回字典键
        #             control.click_box(dictResults[num])
        #             time.sleep(2)
        #             control.click_text("进攻")
        #             timesBattle -= 1
        #             battle()
        #     else:
        #         if timesRefresh > 0:  # 有刷新次数
        #             timesRefresh -= 1
        #             control.click_text("刷新")
        #
        #         else:
        #             break

    def paiqian(self):
        """
        收获：调度室派遣
        """
        locate("调度室")
        box = control.click_text("一键领取")
        if box:
            control.click_box(box)
            control.click_text("再次派遣")
            self.done()

    def qingbaochubei(self):
        """
        收获：情报储备done
        """
        locate("情报储备")
        control.click_text("最大")
        control.click_text("取出")
        self.done()

    def ziyuanshengchan(self):
        """
        收获：资源生产done
        """
        locate("资源生产")
        control.click_text("收取")
        control.click_space()


task = Task()
