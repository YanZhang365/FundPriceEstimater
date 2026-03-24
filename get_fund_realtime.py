# -*- coding: utf-8 -*-
"""
基金实时持仓数据抓取模块(Selenium 驱动）
功能：从东方财富网获取基金实时持仓数据和估算涨跌
"""
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from datetime import datetime


def get_fund_realtime_holdings(fund_code, driver):

    try:
        # 1. 访问持仓明细页面

        url = f"https://fundf10.eastmoney.com/ccmx_{fund_code}.html"
        driver.set_page_load_timeout(5)
        driver.get(url)

        # 2. 等待页面标题加载（验证页面打开成功）
        title_elem = WebDriverWait(driver, 1).until( 
            EC.presence_of_element_located((By.TAG_NAME, "title"))
        )
        full_title = title_elem.text.strip()
        
        # 3. 提取基金名称（格式："XX 基金 (代码) - 持仓明细..." → "XX 基金 代码"）
        fund_name = f"{fund_code} {full_title.split('(')[0].strip()}"

        # 4. 等待动态数据加载
        WebDriverWait(driver, 1).until(  
            EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-id^='zd']"))
        )

        # 5. 快速获取单位净值（优先尝试，不阻塞主流程）      
        bar = WebDriverWait(driver, 1).until(  
            EC.presence_of_element_located((By.CLASS_NAME, "bs_jz"))
        )
        netLabel = bar.find_elements(By.TAG_NAME, "label")
        net_text = ((netLabel[0].text.strip().replace(',', '')).split('：')[1]).strip()
        # 6. 提取表格数据
        holdings = []
        est_fund_increase_pct = 0
        total_holding_pct = 0
        
        rows = driver.find_elements(By.CSS_SELECTOR, "#cctable tr")[1:]  # 跳过表头
        
        for row in rows[:10]:  # 仅取前 10 大持仓
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 7:
                stock_name = cols[2].text.strip()
                stock_code = cols[1].text.strip()
                holding_pct_str = cols[6].text.strip()
                change_pct_str = cols[4].text.strip()
                
                # 跳过数据不全的行（如未开盘）
                if change_pct_str == '-':
                    print(f"[{fund_code}] {stock_name} 数据不全，可能还未开盘")
                    continue
                
                # 转换数值
                holding_pct = float(holding_pct_str.replace("%", ""))
                change_pct = float(change_pct_str.replace("%", ""))
                
                holdings.append({
                    "股票名称": stock_name,
                    "股票代码": stock_code,
                    "持股比例": holding_pct_str,
                    "涨跌幅": change_pct_str
                })
                
                # 累加计算
                total_holding_pct += holding_pct
                est_fund_increase_pct += holding_pct * change_pct

        # 7. 计算加权平均涨跌
        if total_holding_pct > 0:
            est_increase_pct = round(est_fund_increase_pct / total_holding_pct, 3)
        else:
            est_increase_pct = 0

        return {
            "fund_name": fund_name,
            "holdings": holdings,
            "total_holding_pct": round(total_holding_pct, 3),
            "est_increase_pct": est_increase_pct,
            "net": net_text  # 添加当前单价
        }

    except Exception as e:
        print(f"[{fund_code}] 实时持仓爬取失败：{e}")
        return None




def get_funds_realtime_batch(fund_codes, driver, delay=1):
    """
    批量获取多个基金的实时持仓数据
    
    :param fund_codes: 基金代码列表
    :param driver: Selenium WebDriver 实例
    :param delay: 每个基金之间的延时（秒），默认 1 秒
    :return: dict - {基金代码：基金数据}，失败返回空字典
    """
    results = {}
    
    for code in fund_codes:
        try:
            fund_data = get_fund_realtime_holdings(code, driver)
            
            if fund_data:
                results[code] = fund_data
                print(f"✅ {fund_data['fund_name']} | 持仓{fund_data['total_holding_pct']}% | 估算涨跌：{fund_data['est_increase_pct']}%")
            else:
                print(f"❌ 基金 {code} 未获取到实时数据")
            
            time.sleep(delay)  # 防反爬
            
        except Exception as e:
            print(f"❌ 基金 {code} 处理异常：{e}")
            continue
    
    return results


# ==================== 本地调试入口 ====================
if __name__ == "__main__":
    from utils.init_driver import init_driver
    
    # 测试基金代码
    test_codes = ["110022", "000001", "519732"]
    
    print("开始获取基金实时持仓数据...")
    driver = init_driver(browser_type="safari", headless=False)  # 本地调试显示窗口
    
    try:
        results = get_funds_realtime_batch(test_codes, driver, delay=3)
        
        print("\n===== 结果汇总 =====")
        for code, data in results.items():
            print(f"\n{data['fund_name']}:")
            print(f"  总持仓比例：{data['total_holding_pct']}%")
            print(f"  估算涨跌：{data['est_increase_pct']}%")
            print(f"  前 3 大持仓:")
            for holding in data['holdings'][:3]:
                print(f"    {holding['股票名称']} ({holding['股票代码']}): {holding['持股比例']} | {holding['涨跌幅']}")
    
    finally:
        driver.quit()
        print("\n✅ 调试完成，驱动已关闭")
