# -*- coding: utf-8 -*-
"""
基金抓取核心逻辑（仅负责数据抓取和汇总）
"""
from datetime import datetime
import time
import numpy as np
import config  # 导入配置
from get_etf import get_etf_fund_data
from get_otc import get_today_fund_data
from holdings.load_holdings import load_all_fund_holdings
from crawler_otc import init_driver, crawl_fund_daily_return, close_driver

def crawl_otc_funds():
    """抓取所有OTC基金数据"""
    otc_results = {}
    init_driver(browser_type=config.BROWSER_TYPE, headless=config.HEADLESS_MODE)

    all_otc_results = get_today_fund_data()
    all_otc_results_dict = {item["code"]: item for item in all_otc_results}
    print(all_otc_results)
    all_fund_holdings = load_all_fund_holdings('holdings/data')
    all_fund_holdings_dict = {item["code"]: item for item in all_fund_holdings}
    for group_name, fund_codes in config.OTC_FUND_CODES.items():
        otc_results[group_name] = []

        for code in fund_codes:
            fund_holdings = all_fund_holdings_dict[code]
            fund_history = crawl_fund_daily_return(code, config.OTC_CRAWL_DAYS)
            fund_today = all_otc_results_dict.get(code, {})
            if not fund_today:
                print(f"警告：基金 {code} 的数据不存在")
                continue  # 或者跳过这个基金
            otc_res = {**(fund_today or {}), **(fund_holdings or {}), **(fund_history or {})}

            continuous_trend = "未获取到历史数据"
            if fund_history:
                continuous_trend = fund_history.get("连续趋势", continuous_trend)
                otc_res["连续趋势"] = continuous_trend

            # if fund_holdings and fund_holdings.get('total_holding_pct', 0) > 0:
            #     est_fund_increase_pct = 0;
            #     # for holding in fund_holdings.get('holdings', []):
            #     #     stock_pct_chg = next((stock for stock in realtime_stock_price if stock["code"] == code), 0)
            #     #     est_fund_increase_pct += holding['ratio'] * stock_pct_chg
            #     est_change_pct = np.round(est_fund_increase_pct / fund_holdings['total_holding_pct'], 3)
            #     name = fund_holdings['name']
            #     oct_res.update({
            #         "name": name,
            #         "持仓比例(%)": fund_holdings['total_holding_pct'],
            #         "est_change_pct": est_change_pct
            #     })
            # else:
            #     name = fund_holdings.get('name', f"基金{code}")
            #     oct_res.update({
            #         "name": name,
            #         "持仓比例(%)": 0,
            #         "est_change_pct": None,
            #         "持仓状态": "持仓比例为0，或 未获取到实时数据"
            #     })
            #     print(f"基金 {code} 持仓比例为0，或 未获取到实时数据  {continuous_trend}")

            if fund_history:
                otc_res.update({
                    "30天最高价日期": fund_history['最高价日期'],
                    "与天高点%差": fund_history['相对最高价涨跌'],
                    "30天最低价日期": fund_history['最低价日期'],
                    "与30天低点%差": fund_history['相对最低价涨跌']
                })
            else:
                otc_res["30天高低点状态"] = 'no_history_info'
                print(f"基金 {code} 未获取到历史数据")

            otc_results[group_name].append(otc_res)
            time.sleep(3)

    close_driver()
    return otc_results

def run_fund_crawl(trigger_type="定时触发"):
    """核心执行函数：抓取ETF+OTC数据并汇总"""
    exec_start_time = datetime.now()
    print(f"\n===== [{trigger_type}] 开始执行基金数据抓取 at {exec_start_time.strftime('%Y-%m-%d %H:%M:%S')} =====")

    try:
        etf_results = get_etf_fund_data(config.ETF_FUND_CODES)
        print(f"\n===== [{trigger_type}] 开始执行场外基金数据抓取 at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
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
        print(f"执行结束时间：{exec_complete_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"执行时长：{all_fund_data['exec_time']} s")

        return combined_result

    except Exception as e:
        print(f"[{trigger_type}] 基金抓取执行失败：{str(e)}", exc_info=True)
        return {
            "code": -1,
            "msg": f"[{trigger_type}] 抓取失败：{str(e)}",
            "data": {}
        }