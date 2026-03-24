# -*- coding: utf-8 -*-
"""
场外基金(OTC)数据抓取模块（Selenium+Safari/Chrome驱动）
功能：仅提供抓取函数，无硬编码配置，由主文件传参调用
"""
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.safari.options import Options
from selenium.webdriver.chrome.options import Options as ChromeOptions  # 新增：适配云函数Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from io import StringIO
from datetime import datetime, timedelta
import time
import numpy as np

# ==================== 全局驱动变量 ====================
driver = None


# ==================== 初始化驱动（兼容Safari/Chrome，主文件控制） ====================
def init_driver(browser_type="safari", headless=True):
    """
    初始化浏览器驱动（主文件调用，仅初始化一次）
    :param browser_type: safari/chrome，本地用safari，云函数用chrome
    :param headless: 是否无头模式（本地调试可设为False）
    :return: 初始化后的driver
    """
    global driver
    if driver is None:
        if browser_type == "safari":
            safari_options = Options()
            if headless:
                safari_options.add_argument("--headless")
            safari_options.set_capability("safari:automaticInspection", False)
            safari_options.set_capability("safari:automaticProfiling", False)
            driver = webdriver.Safari(options=safari_options)
        elif browser_type == "chrome":
            # 适配腾讯云函数的Chrome无头模式
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=chrome_options)

        # 统一设置超时
        driver.set_page_load_timeout(3)
        driver.implicitly_wait(2)
    return driver



# ==================== 爬取历史涨跌幅+高低点（主文件传参） ====================
def crawl_fund_daily_return(fund_code, past_days=30):
    """
    爬取基金历史净值（主文件传基金代码+回溯天数）
    :param fund_code: 基金代码（主文件传入）
    :param past_days: 回溯天数（主文件控制，默认30天）
    :return: dict - 今日数据、趋势、高低点；失败返回空字典
    """
    if driver is None:
        print(f"[{fund_code}] 驱动未初始化，跳过历史数据抓取")
        return {}

    try:
        url = f"https://fundf10.eastmoney.com/jjjz_{fund_code}.html"
        driver.get(url)
        driver.implicitly_wait(1)

        # 等待表格加载
        table = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CLASS_NAME, "lsjz"))
        )

        # 解析表格
        page_source = driver.page_source
        html_io = StringIO(page_source)
        df_list = pd.read_html(html_io, attrs={"class": "lsjz"})

        if len(df_list) == 0:
            print(f"{fund_code}：未解析到历史净值表格")
            return {}

        df = df_list[0]
        df.columns = ["净值日期", "单位净值", "累计净值", "日涨跌幅", "申购状态", "赎回状态", "分红送配"]
        df = df[df["净值日期"].notna() & df["日涨跌幅"].notna()]
        df["净值日期"] = pd.to_datetime(df["净值日期"], format="%Y-%m-%d", errors="coerce")
        df["日涨跌幅"] = df["日涨跌幅"].str.replace("%", "", regex=False)
        df["日涨跌幅"] = pd.to_numeric(df["日涨跌幅"], errors="coerce")
        df = df[df["净值日期"].notna()]

        # 筛选时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=past_days)
        df_filtered = df[(df["净值日期"] >= start_date) & (df["净值日期"] <= end_date)]
        df_filtered = df_filtered.sort_values("净值日期").reset_index(drop=True)

        if df_filtered.empty:
            print(f"{fund_code}：无{past_days}天内的历史数据")
            return {}

        # 提取核心数据
        today_row = df_filtered.iloc[-1]
        today_date = str(today_row["净值日期"])[:10]
        today_nav = today_row["单位净值"]
        #today_change = today_row["日涨跌幅"] #收盘后值才更新，所以交易日的时候不是当日涨跌幅，是昨日的

        # 统计连续趋势
        consecutive_days = 0
        trend_type = ""
        for idx in reversed(range(len(df_filtered))):
            current_change = df_filtered.iloc[idx]["日涨跌幅"]
            if idx == len(df_filtered) - 1:
                if current_change > 0:
                    trend_type = "涨"
                    consecutive_days += 1
                elif current_change < 0:
                    trend_type = "跌"
                    consecutive_days += 1
                else:
                    trend_type = "平盘"
                    consecutive_days = 0
                    break
            else:
                if trend_type == "涨" and df_filtered.iloc[idx]["日涨跌幅"] > 0:
                    consecutive_days += 1
                elif trend_type == "跌" and df_filtered.iloc[idx]["日涨跌幅"] < 0:
                    consecutive_days += 1
                else:
                    break

        # 计算高低点
        max_nav = df_filtered["单位净值"].max()
        max_nav_date = df_filtered[df_filtered["单位净值"] == max_nav]["净值日期"].dt.strftime("%Y-%m-%d").tolist()[0]
        min_nav = df_filtered["单位净值"].min()
        min_nav_date = df_filtered[df_filtered["单位净值"] == min_nav]["净值日期"].dt.strftime("%Y-%m-%d").tolist()[0]

        change_vs_max = np.round((today_nav - max_nav) / max_nav * 100, 3)
        change_vs_min = np.round((today_nav - min_nav) / min_nav * 100, 3)

        return {
            "net": today_nav,
            #"pct_chg": today_change,
            "trend": f"{trend_type}{consecutive_days}天",
            "trend_days": consecutive_days,
            "trend_type": trend_type,
            "单位净值最高价": max_nav,
            "最高价日期": max_nav_date,
            "单位净值最低价": min_nav,
            "最低价日期": min_nav_date,
            "相对最高价涨跌": change_vs_max,
            "相对最低价涨跌": change_vs_min
        }

    except Exception as e:
        print(f"[{fund_code}] 历史数据爬取失败：{str(e)}")
        return {}


# ==================== 关闭驱动（主文件调用） ====================
def close_driver():
    """关闭驱动（增强版：双重保障）"""
    global driver
    import os
    import signal

    # 第一步：正常退出Selenium驱动
    if driver:
        try:
            driver.quit()  # 关闭整个浏览器，而非单个标签
            print("✅ Selenium驱动已正常退出")
        except Exception as e:
            print(f"⚠️ 正常关闭驱动失败：{e}")
        finally:
            driver = None  # 强制置空

    try:
        # 只杀Selenium相关的Safari进程，不影响手动打开的Safari
        pid_output = os.popen("pgrep -f 'Safari.*WebDriver'").read().strip()
        if pid_output:
            for pid in pid_output.split('\n'):
                if pid:
                    os.kill(int(pid), signal.SIGKILL)
                    print(f"✅ 已强制关闭Safari残留进程（PID：{pid}）")
    except Exception as e:
        print(f"⚠️ 清理Safari进程失败：{e}")


# ==================== 本地调试函数（仅本地测试用） ====================
def local_test(fund_codes, past_days=30):
    """本地调试用，主文件无需调用"""
    init_driver(browser_type="safari", headless=False)  # 本地调试显示浏览器窗口
    for code in fund_codes:
        fund_data = get_fund_holdings(code)
        time.sleep(1)
        fund_history = crawl_fund_daily_return(code, past_days)
        print(f"[{code}] 持仓数据：{fund_data}")
        print(f"[{code}] 历史数据：{fund_history}")
        time.sleep(3)
    close_driver()


# 本地调试入口（仅本地运行时触发，主文件调用时不会执行）
if __name__ == "__main__":
    test_codes = ["519732"]
    local_test(test_codes)