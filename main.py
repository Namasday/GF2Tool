import json
import subprocess
import time

from task import task
from utils import refresh_setting, login


def main():
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
