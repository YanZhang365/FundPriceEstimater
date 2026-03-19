import json
import os
from datetime import datetime


def load_all_fund_holdings(data_dir="data"):
    # 自动推断季度
    now = datetime.now()
    year = now.year
    month = now.month
    q = (month - 1) // 3 + 1
    quarter = f"{year}Q{q}"

    filename = os.path.join(data_dir, f"holdings_{quarter}.json")

    if not os.path.exists(filename):
        print(f"⚠️ 文件不存在: {filename}")
        return None

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("❌ 数据格式错误：根节点必须是列表 (List)")
            return None

        print(f"✅ 成功加载 {quarter} 数据，共 {len(data)} 只基金")
        return data

    except json.JSONDecodeError:
        print(f"❌ JSON 格式损坏，请检查文件: {filename}")
        return None
    except Exception as e:
        print(f"❌ 读取异常: {e}")
        return None


def find_fund_holdings_by_code(fund_code):
    data = load_fund_holdings()
    if data:
        for fund in data:
            # 查找特定基金
            if fund.get("fund_code") == fund_code:
                print(f"\n🔍 找到了目标基金: {fund_code+' '+fund['name']}")
                return fund
        return None
