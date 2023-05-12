# -*- coding: utf-8 -*-
# @Author: xiaocao
# @Date:   2023-04-26 13:25:11
# @Last Modified by:   xiaocao
# @Last Modified time: 2023-05-11 16:50:41

import time
from utils import load_config
from reader import Reader
from threading import Thread


def run():
    config_dict = load_config()

    for account in config_dict["accounts"]:
        Thread(target=Reader(account, config_dict["config"]).run, args=()).start()

    while True:
        time.sleep(60)


if __name__ == "__main__":
    run()

    # nuitka --output-dir=out --follow-imports --standalone --onefile --include-package-data=selenium .\src\start.py
