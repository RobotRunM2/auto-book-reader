# -*- coding: utf-8 -*-
# @Author: xiaocao
# @Date:   2023-04-26 13:30:00
# @Last Modified by:   xiaocao
# @Last Modified time: 2023-05-13 08:50:37

import contextlib
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import logging
import sys


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s - %(message)s",
)


class Reader(object):
    sign_in_day = 0  # 记录签到日期

    def __init__(self, account, config):
        self.account = account
        self.config = config
        self.task_time = config["task_time"]  # 保活次数
        self.keep_live_time = config["keep_live_time"]  # 单个任务时长

        self.task_data = {
            "login": {"tab_handle": None, "count": 0, "max": 1, "func": self._login},
            "sign_in": {
                "tab_handle": None,
                "count": 0,
                "max": 1,
                "func": self._sign_in,
            },
            "read_book": {
                "tab_handle": None,
                "count": 0,
                "max": 999999,
                "func": self.run_task_read_book,
            },
            "listen_book": {
                "tab_handle": None,
                "count": 0,
                "max": 999999,
                "func": self.run_task_listen_book,
            },
            "read_choiceness_book": {
                "tab_handle": None,
                "count": 0,
                "max": 1,
                "func": self.run_task_read_choiceness_book,
            },
        }
        self._init_browser()
        self._init_tabs()

    def add_log_warp(func):
        def wrapper(self, *args, **kwargs):
            logging.info(
                f"account：{self.account['username']} func: {func.__name__} start..."
            )
            func(self, *args, **kwargs)
            logging.info(
                f"account：{self.account['username']} func: {func.__name__} end!"
            )

        return wrapper

    def reset_task_counts(self):
        # 重置任务计数
        self.task_data["login"]["count"] = 0
        self.task_data["sign_in"]["count"] = 0
        self.task_data["read_book"]["count"] = 0
        self.task_data["listen_book"]["count"] = 0
        self.task_data["read_choiceness_book"]["count"] = 0

    @add_log_warp
    def _init_browser(self):
        opt = Options()
        # 设置 opt
        for arg in self.config["options"]:
            opt.add_argument(f"{arg}")

        # opt.add_argument("--no-sandbox")  # 解决DevToolsActivePort文件不存在的报错
        # opt.add_argument("--disable-gpu")  # 谷歌文档提到需要加上这个属性来规避bug
        # opt.add_argument("blink-settings=imagesEnabled=false")  # 不加载图片，提升运行速度
        # opt.add_argument("--headless")  # 浏览器不提供可视化界面。Linux下如果系统不支持可视化不加这条会启动失败

        if self.config["chrome_host"]:
            self.browser = webdriver.Remote(
                command_executor=self.config["chrome_host"], options=opt
            )
        else:
            # 手动指定使用的浏览器位置
            opt.binary_location = f"{self.config['chrome_path']}"

            self.browser = webdriver.Chrome(
                executable_path=self.config["chrome_driver_path"], options=opt
            )

        self.browser.set_window_size(500, 1000)

    @add_log_warp
    def _init_tabs(self):
        # 初始化所有标签页

        tab_items = list(self.task_data.keys())
        for tab_item in tab_items:
            self.task_data[tab_item]["tab_handle"] = self.browser.window_handles[0]

            # if tab_item != tab_items[-1]:
            #     # 不是最后一个就打开一个新标签页
            #     self.browser.execute_script("window.open('')")

    def _click_page(self, x, y, left_click=True):
        """
        dr:浏览器
        x:页面x坐标
        y:页面y坐标
        left_click:True为鼠标左键点击，否则为右键点击
        """
        if left_click:
            ActionChains(self.browser).move_by_offset(x, y).click().perform()
        else:
            ActionChains(self.browser).move_by_offset(x, y).context_click().perform()
        ActionChains(self.browser).move_by_offset(-x, -y).perform()  # 将鼠标位置恢复到移动前

    def _find_element_ex(self, xpath, timeout: int = 10):
        # 等待页面并获取元素
        wait = WebDriverWait(self.browser, timeout=timeout)
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        time.sleep(0.3)
        return element

    def _click_element_ex(self, element):
        # 通过浏览器执行js命令 实现点击
        self.browser.execute_script("arguments[0].click()", element)

    def _find_and_click_ex(self, xpath):
        # 查找并元素点击
        element = self._find_element_ex(xpath, timeout=8)
        self._click_element_ex(element)

    @add_log_warp
    def get_tasks_state(self):
        # 根据页面获取每日任务状态
        self.browser.get("http://weixin.bookan.com.cn/read6/?id=26124#/")

        # 获取每日任务完成状态 ，设置执行情况
        sign_in_text = self._find_element_ex(
            "//body/div[@id='app']/div[1]/div[2]/div[1]/div[4]/div[1]/div[2]"
        ).text
        logging.info(self._log(f"签到任务：{sign_in_text}"))

        read_book_text = self.browser.find_element(
            By.XPATH, "//body/div[@id='app']/div[1]/div[2]/div[1]/div[4]/div[2]/div[2]"
        ).text
        logging.info(self._log(f"读书任务：{read_book_text}"))

        listen_book_text = self.browser.find_element(
            By.XPATH, "//body/div[@id='app']/div[1]/div[2]/div[1]/div[4]/div[3]/div[2]"
        ).text
        logging.info(self._log(f"听书任务：{listen_book_text}"))

        read_choiceness_book_text = self.browser.find_element(
            By.XPATH, "//body/div[@id='app']/div[1]/div[2]/div[1]/div[4]/div[4]/div[2]"
        ).text
        logging.info(self._log(f"读精选书任务：{read_choiceness_book_text}"))

        # --------开始判断
        if sign_in_text == "已完成":
            self.task_data["sign_in"]["count"] = 1
        if read_book_text == "已完成":
            self.task_data["read_book"]["count"] = 1
        if listen_book_text == "已完成":
            self.task_data["listen_book"]["count"] = 1
        if read_choiceness_book_text == "已完成":
            self.task_data["read_choiceness_book"]["count"] = 1

    def _find_close_task_complete_button(self):
        # 任务完成  返回 关闭按钮
        elements = None
        with contextlib.suppress(Exception):
            elements = self._find_element_ex(
                "//body/div[@id='app']/div[3]/div[1]/div[2]/*[1]", timeout=0.8
            )
            logging.info(self._log(f"发现任务完成,{elements}"))
        return elements

    @add_log_warp
    def _login(self):
        """登录账号"""

        # 打开登录窗口
        login_url = "http://wk5.bookan.com.cn/?id=26124&from=%2Fmine#/login"
        # 选择登录窗口
        self.browser.switch_to.window(self.task_data["login"]["tab_handle"])
        self.browser.get(login_url)

        with contextlib.suppress(Exception):
            self._find_and_click_ex("//span[contains(text(),'安全退出')]")
            time.sleep(0.5)
            self._click_page(326, 453)
            self.browser.get(login_url)

        elem_input_username = self._find_element_ex(
            "//body/div[@id='app']/div[2]/div[2]/div[1]/p[1]/input[1]"
        )

        elem_input_password = self.browser.find_element(
            by=By.XPATH,
            value="//body/div[@id='app']/div[2]/div[2]/div[1]/p[2]/input[1]",
        )

        elem_button_login = self.browser.find_element(
            by=By.XPATH,
            value="//body/div[@id='app']/div[2]/div[2]/div[1]/div[1]/p[1]/span[1]",
        )

        elem_input_username.send_keys(self.account["username"])

        elem_input_password.send_keys(self.account["password"])
        elem_button_login.click()

        self._find_element_ex("//span[contains(text(),'安全退出')]")
        time.sleep(0.5)

        self.get_tasks_state()

    @add_log_warp
    def _sign_in(self):
        # 执行签到

        # 选择签到窗口
        self.browser.switch_to.window(self.task_data["sign_in"]["tab_handle"])

        # 打开签到窗口
        sign_in_url = "https://weixin.bookan.com.cn/read6/?id=26124#/sign"
        self.browser.get(sign_in_url)
        time.sleep(0.5)
        # 点击签到按钮
        self._find_and_click_ex("//body/div[@id='app']/div[1]/div[3]")

        time.sleep(0.5)

    @add_log_warp
    def _read_book(self):
        # 选择普通书窗口
        self.browser.switch_to.window(self.task_data["read_book"]["tab_handle"])

        read_book_url = "http://wk5.bookan.com.cn/?id=26124#/column/3"
        self.browser.get(read_book_url)
        time.sleep(1)
        # 点击页面
        self._find_and_click_ex("//*[@id='app']/div[2]/div[1]/div[3]/dl[1]/dd/a[2]")
        time.sleep(0.5)
        # 点击开始阅读

        self._find_and_click_ex("//span[contains(text(),'开始阅读')]")
        time.sleep(0.5)
        self._click_page(450, 500)

    @add_log_warp
    def _read_choiceness_book(self):
        # 读精品书

        # 选择精品书窗口
        self.browser.switch_to.window(
            self.task_data["read_choiceness_book"]["tab_handle"]
        )

        read_choiceness_book_url = (
            "https://weixin.bookan.com.cn/read6/?id=26124#/choosebook"
        )
        self.browser.get(read_choiceness_book_url)
        time.sleep(0.5)
        # 选书

        self._find_and_click_ex(
            "//body/div[@id='app']/div[1]/div[2]/div[1]/div[2]/div[1]"
        )
        # 开始读书
        time.sleep(0.5)
        self._find_and_click_ex("//span[contains(text(),'开始阅读')]")
        time.sleep(0.5)
        self._click_page(450, 500)

    @add_log_warp
    def _listen_book(self):
        # 听书任务
        # 选择听书窗口
        self.browser.switch_to.window(self.task_data["listen_book"]["tab_handle"])

        listen_book_url = "http://wk5.bookan.com.cn/?id=26124#/voice/24"
        self.browser.get(listen_book_url)
        # 选书

        self._find_and_click_ex(
            "//body/div[@id='app']/div[2]/div[2]/dl[1]/dd[1]/a[1]/span[1]"
        )

        time.sleep(0.5)

        # 开始听书
        self._find_and_click_ex("//span[contains(text(),'开始听')]")

        time.sleep(0.5)

        # 展开界面
        self._find_and_click_ex("//body/div[@id='app']/div[3]/i[1]")

    def _stop_listen_book(self):
        # 关闭听书

        #
        self._find_and_click_ex("//span[contains(text(),'返回')]")
        self._find_and_click_ex("//i[contains(text(),'')]")

    @add_log_warp
    def _keep_live_listen_book(self):
        # 保活，避免长时间无操作

        # 选择窗口
        self.browser.switch_to.window(self.task_data["listen_book"]["tab_handle"])

        time.sleep(0.5)
        # 点击上一首按钮
        self._find_and_click_ex("//body/div[@id='app']/div[2]/div[2]/p[3]/span[2]")

    @add_log_warp
    def _keep_live_read_book(self):
        # 保活，避免长时间无操作

        # 选择精品书窗口
        self.browser.switch_to.window(self.task_data["read_book"]["tab_handle"])

        time.sleep(0.5)
        # 随机上下翻页
        x = 50 if bool(random.getrandbits(1)) else 450
        self._click_page(x, 500)

    @add_log_warp
    def _keep_live_read_choiceness_book(self):
        # 保活，避免长时间无操作

        # 选择精品书窗口
        self.browser.switch_to.window(
            self.task_data["read_choiceness_book"]["tab_handle"]
        )

        time.sleep(0.5)
        # 随机上下翻页
        x = 50 if bool(random.getrandbits(1)) else 450
        self._click_page(x, 500)

    def _keep_live_all(self):
        # 执行所以保活
        self._keep_live_listen_book()
        self._keep_live_read_book()
        self._keep_live_read_choiceness_book()

    def _log(self, origin_log):
        now = time.gmtime()
        return f"account: {self.account['username']} {origin_log}"

    def run_task_listen_book(self):
        # 运行听书任务
        self._listen_book()

        if element := self._find_close_task_complete_button():
            self._click_element_ex(element)

        n = 9  # 给一个系数，解决听书频繁保活的问题
        for _ in range(int(self.task_time / n)):
            time.sleep(self.keep_live_time * n)
            if element := self._find_close_task_complete_button():
                self._click_element_ex(element)
            self._keep_live_listen_book()

        self._stop_listen_book()

    def run_task_read_book(self):
        # 运行读书任务
        self._read_book()

        if element := self._find_close_task_complete_button():
            self._click_element_ex(element)

        for _ in range(self.task_time):
            time.sleep(self.keep_live_time)
            if element := self._find_close_task_complete_button():
                self._click_element_ex(element)
            self._keep_live_read_book()

    def run_task_read_choiceness_book(self):
        # 运行都精品书任务
        self._read_choiceness_book()

        if element := self._find_close_task_complete_button():
            self._click_element_ex(element)

        for _ in range(self.task_time):
            time.sleep(self.keep_live_time)
            if element := self._find_close_task_complete_button():
                self._click_element_ex(element)
            self._keep_live_read_choiceness_book()

    def test(self):
        self._login()
        self.browser.get("https://weixin.bookan.com.cn/read6/?id=26124#/")
        self._find_and_click_ex("//body/div[@id='app']/div[1]/div[1]/img[1]")
        self._find_and_click_ex("//body/div[@id='app']/div[1]/div[3]/div[1]/div[2]")

    def run(self):
        from itertools import cycle

        task_data_cycle_iter = cycle(self.task_data.values())
        for task in task_data_cycle_iter:
            # 判断是否为新的一天
            if self.sign_in_day != time.gmtime()[2]:
                self.sign_in_day = time.gmtime()[2]
                self.reset_task_counts()
                logging.info(self._log(f"新的一天开始了，任务重置完成,{self.task_data}"))

            # 执行没有达到最大值的任务
            if task["max"] > task["count"]:
                try:
                    task["func"]()
                    task["count"] += 1
                except Exception as e:
                    logging.info(
                        self._log(
                            f"{task['func'].__name__} ,任务执行异常，当前任务跳过处理！{e.__class__.__name__},{e}"
                        ),
                    )

            time.sleep(1)


# 完成任务弹窗，如果不点击会一直存在
