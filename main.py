#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金抓取主入口（仅负责参数解析、环境配置、信号注册）
"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 添加常用的site-packages路径，解决launchd环境下的模块导入问题
common_paths = [
    f"/usr/local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages",
    f"/opt/homebrew/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages",
    f"/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages",
    f"/Library/Frameworks/Python.framework/Versions/{sys.version_info.major}.{sys.version_info.minor}/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
]

for path in common_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.append(path)

# 再次确认项目根目录在路径中
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import argparse
import signal
import config  # 导入配置
import fund_core  # 导入核心逻辑
from utils import schedule_manager, utils
from datetime import datetime, timedelta
from utils.send_wechat import send_image_to_wechat
from get_market_volume import get_index_data

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
        market_data = get_index_data()  # 获取市场数据
        # 计算总成交量
        sh_data = market_data.get("上证指数", {})
        sz_data = market_data.get("深证成指", {})
        total_volume = (sh_data.get("volume", 0) or 0) + (sz_data.get("volume", 0) or 0)
        # 将成交量转换为万亿单位
        total_volume_trillion = 0
        if total_volume > 0:
            total_volume_trillion = round(total_volume / 1000000000000, 2)
        print(f"总成交量: {total_volume}")
        print(f"总成交量(万亿): {total_volume_trillion}")
        # 构造传递给generate_fund_image的市场数据
        processed_market_data = {
            "volume": total_volume_trillion,
            "sh_current_price": sh_data.get("current_price"),
            "sh_change_pct": str(sh_data.get("change_pct", 0)) + '%' if sh_data.get("change_pct") is not None else "--"
        }
        push_content = utils.generate_fund_image(result, market_data=processed_market_data)
        send_image_to_wechat(f'fund_data_{now.strftime("%Y-%m-%d")}.png')
        print(f"\n手动单次执行完成")
    else:
        # 纯自动定时模式
        # 在定时任务中也需要获取市场数据
        def scheduled_task():
            result = fund_core.run_fund_crawl(trigger_type="定时任务触发")
            market_data = get_index_data()  # 获取市场数据
            # 计算总成交量
            sh_data = market_data.get("上证指数", {})
            sz_data = market_data.get("深证成指", {})
            total_volume = (sh_data.get("volume", 0) or 0) + (sz_data.get("volume", 0) or 0)
            total_volume_trillion = 0
            if total_volume > 0:
                total_volume_trillion = round(total_volume / 1000000000000, 2)
            # 构造传递给generate_fund_image的市场数据
            processed_market_data = {
                "volume": total_volume_trillion,
                "sh_current_price": sh_data.get("current_price"),
                "sh_change_pct": str(sh_data.get("change_pct", 0)) + '%' if sh_data.get("change_pct") is not None else "--"
            }
            utils.generate_fund_image(result, market_data=processed_market_data)
            
        schedule_manager.run_schedule_auto(task_func=scheduled_task)