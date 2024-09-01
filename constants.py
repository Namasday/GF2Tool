import json


class Setting:
    """
    整合所有全局属性
    """
    enlarge = 5  # 局部图像区域放大像素数

    # 键为页面名，值为页面特征文字
    textdictReco = {
        "主界面": "战役推进",
        "班组": "要务",
        "商城": "认购合约",
        "整备室": "云图强固",
        "智能导航光屏": "智能导航光屏",
        "公共区": "调度室",
        "调度室": "调度考核",
        "情报储备": "情报储备情况",
        "资源生产": "每小时产量",
        "班组补给": "班组领取记录",
        "班组要务": "每日要务",
        "设置": "退出账号",
        "登录": "点击开始",
        "限时开启": "定期参与活动可获得丰厚报酬",
        "剧情战役": "猎人评定",
        "模拟作战": "心智勘测",
        "收获": "点击空白处关闭",
        "加载": "资源加载中",
        "作战准备": "作战开始",
        "伤害统计": "伤害统计",
        "任务完成": "任务完成",
        "战斗中": "回合",
        "实兵演习": "布设防御",
        "晋升": "您已晋升至"
    }

    # 路线
    dictLocate = {
        "班组要务": {
            "listPage": ["主界面", "班组", "班组要务"],
            "dictRoute": {
                "主界面": "班组",
                "班组": "要务"
            }
        },
        "班组补给": {
            "listPage": ["主界面", "班组", "班组补给"],
            "dictRoute": {
                "主界面": "班组",
                "班组": "补给"
            }
        },
        "实兵演习": {
            "listPage": ["主界面", "剧情战役", "模拟作战", "实兵演习"],
            "dictRoute": {
                "主界面": "战役推进",
                "剧情战役": "模拟作战",
                "模拟作战": "实兵演习"
            }
        },
        "调度室": {
            "listPage": ["主界面", "公共区", "调度室"],
            "dictRoute": {
                "主界面": "公共区",
                "公共区": "调度室"
            }
        },
        "情报储备": {
            "listPage": ["主界面", "公共区", "调度室", "情报储备"],
            "dictRoute": {
                "主界面": "公共区",
                "公共区": "调度室",
                "调度室": "调度收益"
            }
        },
        "资源生产": {
            "listPage": ["主界面", "公共区", "调度室", "情报储备", "资源生产"],
            "dictRoute": {
                "主界面": "公共区",
                "公共区": "调度室",
                "调度室": "调度收益",
                "情报储备": "资源生产"
            }
        }
    }

    hwnd = None  # 窗口句柄
    windowPosition = None  # 窗口位置
    windowBar = None  # 窗口是否有标题栏
    titleBarHeight = 58  # 标题栏高度
    threshold = 0.8  # 识别置信度阈值
    fightingCapacity = 5000  # 战力阈值
    dictTemplate = {
        "自动战斗": "template/autobattle.png",
        "自动战斗中": "template/autobattlein.png"
    }  # 模板图片指针

    # 读取预设文件
    with open("config.json", "r") as f:
        data = json.load(f)

    timeslimitBattle = data['timeslimitBattle']  # 战斗次数限制
    screenWidth = data['screenWidth']  # 屏幕分辨率
    screenHeight = data['screenHeight']  # 屏幕分辨率
    scaleFactor = data['scaleFactor']  # 屏幕缩放系数
