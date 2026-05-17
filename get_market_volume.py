# -*- coding: utf-8 -*-
"""
市场指数和板块涨跌幅数据抓取模块
功能：获取大盘指数和指定板块的涨跌幅
数据源：腾讯财经、东方财富网
"""
import requests
import time
from datetime import datetime


def get_tencent_market_data(market_code, market_name):
    """
    从腾讯财经获取指数数据
    
    :param market_code: 指数代码
    :param market_name: 指数名称
    :return: dict - 指数数据
    """
    try:
        url = f"http://qt.gtimg.cn/q={market_code}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gbk'  # 腾讯返回 GBK 编码
        
        # 解析数据格式：v_sh000001="51~上证指数~000001~3050.12~3060.45~..."
        text = response.text.strip()
        if not text or '=' not in text:
            return None
        
        parts = text.split('"')[1].split('~')
        
        if len(parts) < 40:
            return None
        
        current_price = float(parts[3]) if parts[3] else 0
        yesterday_price = float(parts[4]) if parts[4] else 0
        volume = float(parts[6]) if parts[6] else 0  # 成交量
        turnover = float(parts[7]) if parts[7] else 0  # 成交额
        
        change_pct = 0
        if yesterday_price > 0:
            change_pct = round(((current_price - yesterday_price) / yesterday_price) * 100, 2)
        
        return {
            "name": market_name,
            "code": market_code,
            "current_price": current_price,
            "change_pct": change_pct,
            "volume": volume,
            "turnover": turnover,
            "yesterday_price": yesterday_price,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        print(f"获取 {market_name} 数据失败：{e}")
        return None


def get_index_data(date=None):
    """
    获取上证指数和深证成指的当前价、涨跌幅、成交量、成交额
    
    :param date: 日期字符串，格式为 "YYYY-MM-DD"，如果为None则获取实时数据
    :return: dict - 包含上证指数和深证成指数据
    """
    if date is not None:
        # 这里可以添加历史数据获取逻辑，暂时返回提示信息
        return {
            "error": f"指定日期 {date} 的数据暂不支持，请使用实时数据"
        }
    
    indices = [
        # ("sh000001", "上证指数"),
        # ("sz399001", "深证成指")
        ("sh_total", "沪市总成交额"),
        ("sz_total", "深市总成交额")
    ]
    
    results = {}
    
    for code, name in indices:
        index_data = get_tencent_market_data(code, name)
        if index_data:
            results[name] = {
                "current_price": index_data["current_price"],
                "change_pct": index_data["change_pct"],
                "volume": index_data["volume"],
                "turnover": index_data["turnover"]
            }
        else:
            results[name] = {
                "current_price": None,
                "change_pct": None,
                "volume": None,
                "turnover": None,
                "error": "没开盘或数据获取失败"
            }
    
    return results


def get_eastmoney_sector_data(sector_name):
    """
    从东方财富网获取板块数据
    
    :param sector_name: 板块名称
    :return: dict - 板块数据
    """
    try:
        # 根据板块名称映射到具体的板块代码
        sector_map = {
            "通信设备": "BK0448",
            "机器人": "BK0927", 
            "创新药": "BK0722",
            "工业金属": "BK1287",
            "电网设备": "BK0478",
            "商业航天": "BK1045",
            "港股科技": "BK0707"
        }
        
        sector_code = sector_map.get(sector_name)
        if not sector_code:
            print(f"未找到 {sector_name} 对应的板块代码")
            return None

        secid = f"90.{sector_code}"
        url = "http://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "secid": secid,
            "fields": "f43,f44,f45,f46,f47,f17,f116,f117,f118,f57,f58,f3,f8,f9,f10,f11,f12,f13,f14,f15,f16",
            "_": int(time.time() * 1000)
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('data') is None:
            print(f"获取 {sector_name} 数据失败，响应内容：{data}")
            return None
        
        result = data['data']
        current_price = result.get('f43', 0)  # 当前价
        change_pct = result.get('f3', 0)  # 涨跌幅
        name = result.get('f58', sector_name)  # 板块名称
        
        return {
            "name": name,
            "code": sector_code,
            "current_price": current_price,
            "change_pct": change_pct,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        print(f"获取 {sector_name} 数据失败：{e}")
        return None


def get_sector_data(date=None):
    """
    获取指定板块的数据
    
    :param date: 日期字符串，格式为 "YYYY-MM-DD"，如果为None则获取实时数据
    :return: dict - 包含各板块数据
    """
    if date is not None:
        # 这里可以添加历史数据获取逻辑，暂时返回提示信息
        return {
            "error": f"指定日期 {date} 的板块数据暂不支持，请使用实时数据"
        }
    
    target_sectors = [
        "通信设备",
        "商业航天", 
        "机器人",
        "创新药",
        "港股科技",
        "工业金属",
        "电网设备"
    ]
    
    results = {}
    
    for sector_name in target_sectors:
        sector_data = get_eastmoney_sector_data(sector_name)
        if sector_data and 'current_price' in sector_data:
            results[sector_name] = {
                "current_price": sector_data["current_price"],
                "change_pct": sector_data["change_pct"]
            }
        else:
            results[sector_name] = {
                "current_price": None,
                "change_pct": None,
                "error": "数据获取失败"
            }
        time.sleep(0.5)  # 避免请求过快
    
    return results


def test_functions():
    """
    测试函数
    """
    print("=" * 60)
    print("测试获取指数数据")
    print("=" * 60)
    
    index_results = get_index_data()
    for index_name, data in index_results.items():
        if "error" in data:
            print(f"{index_name}: {data['error']}")
        else:
            print(f"{index_name}:")
            print(f"  当前价: {data['current_price']:.2f}")
            print(f"  涨跌幅: {data['change_pct']:+.2f}%")
            print(f"  成交量: {data['volume']:.2f}")
            print(f"  成交额: {data['turnover']:.2f}")
    
    print("\n" + "=" * 60)
    print("测试获取板块数据")
    print("=" * 60)
    
    sector_results = get_sector_data()
    for sector_name, data in sector_results.items():
        if "error" in data:
            print(f"{sector_name}: {data['error']}")
        else:
            print(f"{sector_name}:")
            print(f"  当前价: {data['current_price']:.2f}")
            print(f"  涨跌幅: {data['change_pct']:+.2f}%")


# ==================== 测试入口 ====================
if __name__ == "__main__":
    test_functions()