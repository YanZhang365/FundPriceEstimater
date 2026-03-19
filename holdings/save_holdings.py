import json
import os
from datetime import datetime
import time
import config  # 导入配置
from get_holdings import get_fund_holdings

from utils.init_driver import init_driver # 导入核心逻辑

def save_fund_holdings(holdings_data, output_dir="data"):
    # 自动推断季度
    now = datetime.now()
    year = now.year
    month = now.month
    q = (month - 1) // 3 + 1
    quarter = f"{year}Q{q}"

    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, f"holdings_{quarter}.json")

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(holdings_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 持仓数据已成功保存至: {filename}")
    except Exception as e:
        print(f"❌ 保存失败: {e}")

#==================== 入口 ====================
if __name__ == "__main__":

    exec_start_time = datetime.now()
    # 全局驱动变量
    driver = init_driver(browser_type=config.BROWSER_TYPE, headless=config.HEADLESS_MODE)

    fund_holdings = []
    try:
        for group_name, fund_codes in config.OTC_FUND_CODES.items():
            print(f"\n===== 开始抓取 [{group_name}] 组 基金前10持仓 =====")

            for code in fund_codes:
                fund_data = get_fund_holdings(driver, code)

                if fund_data:  # 确保数据有效才加入
                    fund_holdings.append(fund_data)
                    if len(fund_data['holdings'])>0:
                        print(f"  - 成功获取 {code}: {fund_data['name']}")

                time.sleep(1)  # 控制爬取频率
        # 保存所有基金的数据
        if fund_holdings:
            save_fund_holdings(fund_holdings)
            print(f"\n🎉 共获取 {len(fund_holdings)} 只基金数据")
        else:
            print("\n❌ 未能获取到任何基金数据")

    finally:

        exec_complete_time = datetime.now()
        print(f"执行时长：{(exec_complete_time - exec_start_time).total_seconds()}s");
        # 记得关闭浏览器
        if driver:
            driver.quit()
