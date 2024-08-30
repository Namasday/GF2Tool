# 键为界面名，值为下一界面名字典
from constants import Setting
from utils import ocr, TargetPosition, screenshot, refresh_setting, crop_image

dictPages = {
    "主界面": {
        "剧情战役": "战役推进",
        "班组": "班组",
        "公共区": "公共区"
    },
    "智能导航光屏": {
        "剧情战役": "剧情战役",
        "公共区": "公共区"
    },
    "班组": {
        "班组要务": "要务",
        "班组补给": "补给"
    },
    "公共区": {
        "调度室": "调度室"
    },
    "调度室": {
        "情报储备": "调度收益"
    },
    "情报储备": {
        "资源生产": "资源生产"
    },
}


class ShiBingYanXi:
    """
    实兵演习进攻各玩家界面
    """
    # def __init__(self, img, index):
    #     ratio = Setting.screenWidth / 3840
    #     listX = [490,1080,1680,2270,2870]
    #     self.x1 = listX[index] * ratio
    #     self.y1 = 1010 * ratio
    #     self.width = 340 * ratio
    #     self.height = 240 * ratio
    #     self.img = img[self.y1:self.y1+self.width, self.x1:self.x1+self.height]
    #     self.dictResults = {}
    #     self.ocr()

    def check_battletimes(self):
        """
        检查战斗次数
        """
        img = screenshot()  # 截图
        imgBattleTimes = crop_image(img, area=(3650, 60, 3740, 110))
        timesBattle = int(ocr(imgBattleTimes.image)[0][0][1][0])
        return timesBattle

    def ocr(self):
        """识别与分类"""
        listResults = ocr(self.img)[0]

        for result in listResults:
            box = result[0]
            text = result[1]
            confidence = result[2]

            self.dictResults[text] = TargetPosition(
                x1=box[0][0] + self.x1,
                y1=box[0][1] + self.y1,
                x2=box[2][0] + self.x1,
                y2=box[2][1] + self.y1,
                confidence=confidence,
            )


if __name__ == "__main__":
    refresh_setting()
    instance = ShiBingYanXi()
