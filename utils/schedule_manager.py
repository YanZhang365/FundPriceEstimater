# -*- coding: utf-8 -*-
"""
定时任务管理器（负责定时执行、自动退出、防休眠）
"""
import schedule
import time
import sys
import subprocess
import config  # 导入配置
import fund_core  # 导入核心抓取逻辑
import utils


def disable_mac_sleep():
    """禁用mac休眠（程序运行期间）"""
    try:
        # 启动caffeinate进程，后台运行
        sleep_process = subprocess.Popen(
            ["caffeinate", "-s", "-u"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✅ mac休眠已临时禁用（程序退出后自动恢复）")
        return sleep_process
    except Exception as e:
        print(f"⚠️  禁用休眠失败：{e}，可能影响定时执行")
        return None

def enable_mac_sleep(sleep_process):
    """恢复mac休眠"""
    if sleep_process:
        try:
            sleep_process.terminate()
            print("✅ mac休眠已恢复")
        except:
            pass

def stop_program(trigger_type="手动退出", sleep_process=None):
    """停止程序：恢复休眠 + 释放资源"""
    config.GLOBAL_RUN_FLAG = False
    print(f"\n===== [{trigger_type}] 开始退出程序 =====")

    # 恢复mac休眠
    if sleep_process:
        try:
            sleep_process.terminate()
            print("✅ mac休眠已恢复")
        except:
            pass

    # 关闭浏览器驱动
    print("正在释放资源（关闭浏览器驱动）...")
    try:
        from crawler_otc import close_driver
        close_driver()
    except:
        pass

    print(f"[{trigger_type}] 程序已正常退出！")
    sys.exit(0)


def run_schedule_auto():
    """纯自动定时模式：防休眠 + 启动立即执行 + 定时执行"""
    # 1. 禁用mac休眠
    sleep_process = disable_mac_sleep()

    # 2. 启动后立即执行一次抓取
    fund_core.run_fund_crawl(trigger_type="启动立即执行")

    # 3. 添加定时执行任务
    for t in config.SCHEDULE_TIME:
        schedule.every().day.at(t).do(fund_core.run_fund_crawl, trigger_type="定时触发")

    # 4. 添加自动退出任务
    schedule.every().day.at(config.AUTO_EXIT_TIME).do(stop_program, trigger_type="自动退出",
                                                      sleep_process=sleep_process)

    # 5. 打印启动日志
    print("=" * 60)
    print(f"基金抓取定时程序已启动（macOS版）")
    print(f"定时执行时间：{config.SCHEDULE_TIME}")
    print(f"自动退出时间：{config.AUTO_EXIT_TIME}")
    print(f"手动退出：按 Control+C 即可强制退出")
    print("=" * 60)

    # 6. 后台循环检测定时任务
    while config.GLOBAL_RUN_FLAG:
        schedule.run_pending()
        time.sleep(60)  # 每60秒检查一次