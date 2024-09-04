import json


class Setting:
    """
    整合所有全局属性
    """
    titleBarHeight = 58  # 标题栏高度
    threshold = 0.8  # 识别置信度阈值
    dictTemplatePath = {
        "返回主界面_黑": "template/return_black.png",
        "返回主界面_白": "template/return_white.png",
        "自动战斗": "template/autobattle.png",
        "关闭要务": "template/close_yaowu.png",
        "关闭进攻选择": "template/back_jingongxuanze.png",
        "收获_演习": "template/reward_yanxi.png"
    }  # 模板图片指针

    # 读取预设文件
    with open("config.json", "r") as f:
        data = json.load(f)

    timeslimitBattle = data['timeslimitBattle']  # 战斗次数限制
    limitCapacity = data['limitCapacity']  # 战力阈值
    limitRank = data['limitRank']  # 排名限制
    screenWidth = data['screenWidth']  # 屏幕分辨率宽度
    screenHeight = data['screenHeight']  # 屏幕分辨率高度
    scaleFactor = data['scaleFactor']  # 缩放比例
