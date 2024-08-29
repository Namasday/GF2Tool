from control import control
from utils import refresh_setting, reco_page, logger


class Task:
    def banzu_yaowu(self):
        route = ["主界面", "班组", "班组要务"]
        dictrouteBanzuYaowu = {
            "主界面": "班组",
            "班组": "要务"
        }
        locate("班组要务")


task = Task()


if __name__ == "__main__":
    running = refresh_setting()
    if running:
        task.banzu_yaowu()
