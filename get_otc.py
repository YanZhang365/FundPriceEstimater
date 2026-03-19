import json
from datetime import datetime

import akshare as ak
import numpy as np
import pandas as pd


def get_today_fund_data():
    try:

        fund = ak.fund_open_fund_daily_em()# 开放式基金
        # fund = ak.fund_etf_category_ths(symbol="ETF", date="20240620")
        print("fund_open_fund_daily_em------------------", fund)
        if fund.empty:
            print("获取到的股票数据为空")
            return []
        now = datetime.now()
        column_name = f"{now.strftime("%Y-%m-%d")}-单位净值"
        result = []
        for _, row in fund.iterrows():
            # if row['基金代码'] in codes:
                stock_info = {
                    "code": str(row['基金代码']),  # 股票代码
                    "name": row['基金简称'],  # 股票名称
                    "net": str(row[column_name]),  # 当前价格
                    "ratio": pd.to_numeric(row['日增长率']),  # 涨跌幅度百分比
                }
                result.append(stock_info)
        return result

    except Exception as e:
        print(f"获取数据失败: {str(e)}")
        return []


# 测试获取数据
if __name__ == "__main__":
    print("正在获取股票数据...")
    stock_list = get_today_fund_data(["003096", "161726", "019127", "005689"])#
    print(f"共获取到 {len(stock_list)} 只股票数据")

    # 打印前5条数据示例
    for i, stock in enumerate(stock_list[:5]):
        print(f"{i + 1}. {stock}")