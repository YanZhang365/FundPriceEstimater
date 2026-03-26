# -*- coding: utf-8 -*-
"""
基金抓取核心逻辑（仅负责数据抓取和汇总）
"""
from datetime import datetime
import time
import numpy as np
import config  # 导入配置
from get_etf import get_etf_fund_data
from holdings.load_holdings import load_all_fund_holdings
from crawler_otc import init_driver, crawl_fund_daily_return, close_driver
from get_fund_realtime import get_fund_realtime_holdings

def crawl_otc_funds():
    """抓取所有 OTC 基金数据"""
    otc_results = {}
    driver = init_driver(browser_type=config.BROWSER_TYPE, headless=config.HEADLESS_MODE)

    all_fund_holdings = load_all_fund_holdings('holdings/data')
    all_fund_holdings_dict = {item["code"]: item for item in all_fund_holdings}
    for group_name, fund_codes in config.OTC_FUND_CODES.items():
        otc_results[group_name] = []

        for code in fund_codes:
            try:
                # ① 获取实时持仓数据（每个基金单独调用）
                fund_realtime = get_fund_realtime_holdings(code, driver)
                # ② 获取历史净值数据
                fund_history = crawl_fund_daily_return(code, config.OTC_CRAWL_DAYS)
                # ③ 加载本地持仓配置
                fund_holdings = all_fund_holdings_dict.get(code, {})
                if not fund_realtime:
                    print(f"⚠️  基金 {code} 未获取到实时数据")
                    # 降级方案：仅保留基本信息
                    otc_res = {
                        "code": code,
                        "name": fund_holdings.get("name", f"基金{code}"),
                        "实时数据状态": "获取失败"
                    }
                else:
                    otc_res = {
                        **fund_holdings,
                        **fund_realtime
                    }
                    otc_res.update({
                        "net":  fund_realtime.get("net"), 
                        "ratio": fund_realtime.get("est_increase_pct")
                    })
                if fund_realtime:
                    fund_history = crawl_fund_daily_return(code, 30)
                    if fund_history:
                        continuous_trend = fund_history.get("trend", "未获取到历史数据")
                        otc_res["trend"] = continuous_trend
                        otc_res.update({
                            "30天最高价日期": fund_history['最高价日期'],
                            "与30天高点%差": fund_history['相对最高价涨跌'],
                            "30天最低价日期": fund_history['最低价日期'],
                            "与30天低点%差": fund_history['相对最低价涨跌']
                        })
                        print(f"✅ {fund_realtime['fund_name'].ljust(25)} | 持仓{fund_realtime['total_holding_pct']}% | 估算涨跌：{fund_realtime['est_increase_pct']}% | {continuous_trend}")
                    else:
                        print(f"✅ {fund_realtime['fund_name'].ljust(25)} | 持仓{fund_realtime['total_holding_pct']}% | 估算涨跌：{fund_realtime['est_increase_pct']}% | 无历史数据")
                else:
                    print(f"⚠️  基金 {code} 实时数据缺失（保留基本信息）")

                otc_results[group_name].append(otc_res)
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ 基金 {code} 处理异常：{e}")
                continue

    close_driver()
    return otc_results

def run_fund_crawl(trigger_type="定时触发"):
    """核心执行函数：抓取 ETF+OTC 数据并汇总"""
    exec_start_time = datetime.now()
    print(f"\n===== [{trigger_type}] 开始执行基金数据抓取 at {exec_start_time.strftime('%Y-%m-%d %H:%M:%S')} =====")

    try:
        print(f"\n===== ETF =====")
        etf_results = get_etf_fund_data(config.ETF_FUND_CODES)
        print(f"\n===== 场外基金 =====")
        otc_results = crawl_otc_funds()

        exec_complete_time = datetime.now()
        all_fund_data = {
            "exec_time": (exec_complete_time - exec_start_time).total_seconds(),
            "etf_fund": etf_results,
            "otc_fund": otc_results,
            "total_etf_count": len(config.ETF_FUND_CODES),
            "total_otc_count": sum([len(codes) for codes in config.OTC_FUND_CODES.values()])
        }
        combined_result = {**{"ETF":etf_results},**otc_results}
        print(f"\n===== [{trigger_type}] 抓取完成汇总 =====")
        print(f"执行结束时间：{exec_complete_time.strftime('%Y-%m-%d %H:%M:%S')}, 执行时长：{all_fund_data['exec_time']} s")

        return combined_result

    except Exception as e:
        print(f"[{trigger_type}] 基金抓取执行失败：{str(e)}", exc_info=True)
        return {
            "code": -1,
            "msg": f"[{trigger_type}] 抓取失败：{str(e)}",
            "data": {}
        }