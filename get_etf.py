# -*- coding: utf-8 -*-
"""场内ETF基金数据抓取模块"""
import akshare as ak
import random
from time import sleep
import pandas as pd
from datetime import datetime, timedelta


def get_etf_fund_data(codes):
    """
    获取场内ETF基金实时数据+30天高低价差值百分比
    :param codes: list - 场内ETF基金代码列表（如['159819', '515230', '159869', '513160']）
    :return: dict - 键：基金代码，值：包含类型、名称、涨跌幅、30天高低价百分比的字典
    """
    # 初始化返回字典（键=代码，值=信息字典）
    etf_data = []

    # 获取全量ETF列表（新浪接口，用于匹配实时数据）
    try:
        all_etf_info = ak.fund_etf_category_sina(symbol="ETF基金")
    except Exception as e:
        print(f"【ETF模块】获取全量ETF列表失败：{str(e)}")
        return etf_data

    # 计算30天前的日期（用于筛选历史数据）
    thirty_days_ago = datetime.now() - timedelta(days=30)

    # 遍历每个ETF代码抓取数据
    for code in codes:
        # 初始化单只ETF信息字典（保留原始字段顺序）
        fund_info = {
            "code": code,
            "type": None,
            "name": None,
            "net": None,  # 当前价/最新价
            "ratio": None,  # 涨跌幅
            "time": None,  # 数据更新时间
            "30d_high": None,  # 当前价较30天最高价的差值百分比
            "30d_low": None  # 当前价较30天最低价的差值百分比
        }

        # 防反爬延迟（1-2秒随机）
        sleep(random.uniform(1, 2))

        try:
            # 匹配基金代码（兼容sh/sz前缀）
            etf_info_df = all_etf_info[
                (all_etf_info['代码'] == code) |
                (all_etf_info['代码'] == f"sh{code}") |
                (all_etf_info['代码'] == f"sz{code}")
                ]

            if not etf_info_df.empty:
                # 填充基础信息
                fund_info["type"] = "场内ETF"
                fund_info["name"] = etf_info_df["名称"].iloc[0]
                fund_info["ratio"] = etf_info_df["涨跌幅"].iloc[0]
                fund_info["net"] = etf_info_df["最新价"].iloc[0]
                fund_info["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 计算30天高低价与当前价的差值百分比
                try:
                    # 获取ETF历史日线数据（纯数字代码，无需前缀）
                    etf_hist_df = ak.fund_etf_hist_em(
                        symbol=code,
                        period="daily"
                    )

                    if not etf_hist_df.empty:
                        # 转换日期格式并筛选30天内数据
                        etf_hist_df['日期'] = pd.to_datetime(etf_hist_df['日期'])
                        recent_30d_df = etf_hist_df[etf_hist_df['日期'] >= thirty_days_ago]

                        if not recent_30d_df.empty:
                            # 排除停牌/无效数据（收盘价>0）
                            valid_30d_df = recent_30d_df[recent_30d_df["收盘"] > 0]

                            if not valid_30d_df.empty:
                                # 提取30天最高/最低价（原始价格）
                                high_30d = valid_30d_df["最高"].max()
                                low_30d = valid_30d_df["最低"].min()

                                # 处理当前价（转为浮点数，避免非数字值）
                                current_price = None
                                if fund_info["net"] is not None and str(fund_info["net"]).replace('.', '').isdigit():
                                    current_price = float(fund_info["net"])

                                # 计算差值百分比
                                if current_price is not None and current_price != 0:
                                    pct_high = round(((current_price - high_30d) / high_30d) * 100, 2)
                                    pct_low = round(((current_price - low_30d) / low_30d) * 100, 2)

                                    # 存入百分比结果
                                    fund_info["与30天高点%差"] = pct_high
                                    fund_info["与30天低点%差"] = pct_low

                                    # 打印日志（便于调试）
                                    print(f"{code} {fund_info['name']}- {fund_info['ratio']}%  "
                                          f"近30天最高价差% {pct_high}%，近30天最低价差% {pct_low}%")
                                else:
                                    print(f"【ETF模块】{code} - 当前价无效（{fund_info['net']}），无法计算差值百分比")
                            else:
                                print(f"【ETF模块】{code} - 最近30天无有效收盘数据（全是停牌）")
                        else:
                            print(f"【ETF模块】{code} - 无最近30天数据（上市不足30天）")
                except Exception as hist_e:
                    print(f"【ETF模块】{code} - 30天高低价获取失败：{hist_e}")

            else:
                print(f"【ETF模块】{code} - 未找到匹配数据")

        except Exception as e:
            fund_info["error"] = str(e)  # 记录异常信息
            print(f"【ETF模块】{code} 爬取失败：{str(e)}")

        # 将单只ETF信息加入返回字典
        etf_data.append(fund_info)

    return etf_data


# 测试获取数据
if __name__ == "__main__":
    print("正在获取基金数据...")
    etf_list = get_etf_fund_data(['159819', "515230", "159869", "513160", "518800"])
    print(f"共获取到 {len(etf_list)} 只基金数据")

    # 打印前5条数据示例
    for i, stock in enumerate(etf_list[:5]):
        print(f"{i + 1}. {stock}")