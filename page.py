# 键为界面名，值为下一界面名字典
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


class Page:
    def __init__(self, pagename, dictNextPage):
        # 界面名
        self.pagename = pagename

        # 键为下一界面名称，值为当前界面跳转至对应界面的按钮文本
        self.dictNextPage = dictNextPage


def create_instance():
    for key, value in dictPages.items():
        dictPages[key] = Page(pagename=key, dictNextPage=value)


create_instance()
