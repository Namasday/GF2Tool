import json
import subprocess
import time

from task import task
from utils import refresh_setting, login


def main():
    with open('config.json', 'r') as f:
        data = json.load(f)

    running = refresh_setting()
    if not running:  # 如果游戏未运行，则启动游戏
        subprocess.Popen(data['gamepath'])
        time.sleep(15)
        refresh_setting()

    # login()
    # task.paiqian()
    # task.ziyuanshengchan()
    # task.qingbaochubei()
    # task.banzu_yaowu()
    # task.banzu_buji()
    task.shibingyanxi()


if __name__ == '__main__':
    main()
