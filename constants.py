import json


class Setting:
    """
    整合所有全局属性
    """
    enlarge = 5  # 局部图像区域放大像素数

    # 键为页面名，值为页面特征文字
    textdictReco = {
        "商城": "认购合约",
        "整备室": "云图强固",
        "智能导航光屏": "智能导航光屏",
        "公共区": "调度室",
        "调度室": "调度考核",
        "情报储备": "情报储备情况",
        "资源生产": "每小时产量",
        "设置": "退出账号",
        "登录": "点击开始",
        "限时开启": "定期参与活动可获得丰厚报酬",
        "收获": "点击空白处关闭",
        "加载": "资源加载中",
        "作战准备": "作战开始",
        "伤害统计": "伤害统计",
        "任务完成": "任务完成",
        "战斗中": "回合",
        "晋升": "您已晋升至"
    }

    titleBarHeight = 58  # 标题栏高度
    threshold = 0.8  # 识别置信度阈值
    fightingCapacity = 5000  # 战力阈值
    dictTemplatePath = {
        "返回主界面_黑": "template/return_black.png",
        "返回主界面_白": "template/return_white.png",
        "自动战斗": "template/autobattle.png",
        "自动战斗中": "template/autobattlein.png"
    }  # 模板图片指针

    # 读取预设文件
    with open("config.json", "r") as f:
        data = json.load(f)

    timeslimitBattle = data['timeslimitBattle']  # 战斗次数限制
    screenWidth = data['screenWidth']  # 屏幕分辨率宽度
    screenHeight = data['screenHeight']  # 屏幕分辨率高度
    scaleFactor = data['scaleFactor']  # 缩放比例
