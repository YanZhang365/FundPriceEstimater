# -*- coding: utf-8 -*-
"""
基金抓取主入口（仅负责参数解析、环境配置、信号注册）
"""
import argparse
import signal
import config  # 导入配置
import fund_core  # 导入核心逻辑
from utils import schedule_manager, utils
from datetime import datetime, timedelta
from utils.send_wechat import send_image_to_wechat
# ==================== 信号捕获（Control+C强制退出） ====================
def signal_handler(signal_num, frame):
    """捕获Control+C，调用退出逻辑"""
    schedule_manager.stop_program(trigger_type="Control+C强制退出")

# 注册SIGINT信号
signal.signal(signal.SIGINT, signal_handler)

# ==================== 腾讯云函数入口 ====================
def main_handler(event, context):
    """腾讯云函数SCF入口"""
    # 云函数环境配置
    config.BROWSER_TYPE = "chrome"
    config.HEADLESS_MODE = True
    return fund_core.run_fund_crawl(trigger_type="云函数触发")

# ==================== 本地主入口 ====================
if __name__ == "__main__":
    # 1. 解析命令行参数
    parser = argparse.ArgumentParser(description="基金抓取程序（macOS纯自动版）")
    parser.add_argument("--mode", choices=["once", "schedule"], default="schedule",
                        help="运行模式：once=手动单次执行 | schedule=纯自动定时（15:10退出）")
    args = parser.parse_args()

    # 2. 本地环境配置
    config.BROWSER_TYPE = "safari"
    config.HEADLESS_MODE = False  # 本地显示浏览器窗口

    # 3. 根据模式执行
    if args.mode == "once":
        # 单次执行模式
        result = fund_core.run_fund_crawl(trigger_type="手动单次触发")
        now = datetime.now()
        push_content = utils.generate_fund_image(result)
        send_image_to_wechat(f'fund_data_{now.strftime("%Y-%m-%d")}.png')
        print(f"\n手动单次执行完成")
    else:
        # 纯自动定时模式
        schedule_manager.run_schedule_auto()