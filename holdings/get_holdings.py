
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import numpy as np

def get_fund_holdings(driver, fund_code):

    if driver is None:
        print(f"[{fund_code}] 驱动未初始化，跳过抓取")
        return None

    try:
        url = f"https://fundf10.eastmoney.com/ccmx_{fund_code}.html"
        driver.get(url)

        # ----- 1.提取基金名称 -----
        try:
            title_elem = WebDriverWait(driver, 4).until(
                EC.presence_of_element_located((By.TAG_NAME, "title"))
            )
            full_title = title_elem.text.strip()
            fund_name = f"{full_title.split('(')[0]}"
            # 确认页面不是错误页（检查标题是否包含错误关键词）
            if any(keyword in full_title.lower() for keyword in ["错误", "404", "not found"]):
                print(f"[{fund_code}] 标题包含错误信息: {full_title}，跳过")
                return {
                    "code": fund_code,
                    "name": '',
                    "holdings": [],
                    "total_holding_pct": 0
                }

        except TimeoutException:
            print(f"[{fund_code}] 获取基金名称超时，可能页面加载失败，跳过")
            return {
                "code": fund_code,
                "name": fund_name | '',
                "holdings": [],
                "total_holding_pct": 0
            }

        # ----- 2.等待持仓表格加载 -----
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-id^='zd']"))
            )

            # 解析持仓数据
            holdings = []
            total_holding_pct = 0.0
            rows = driver.find_elements(By.CSS_SELECTOR, "#cctable tr")[1:]
            if len(rows) == 0:
                print(f"[{fund_code}] 解析时发现表格无数据行，跳过")
                return {
                    "code": fund_code,
                    "name": fund_name,
                    "holdings": [],
                    "total_holding_pct": 0
                }
            for row in rows[:10]:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 6:
                    stock_name = cols[2].text.strip()
                    stock_code = cols[1].text.strip()
                    hold_pct = cols[6].text.strip()

                    holdings.append({
                        "name": stock_name,
                        "code": stock_code,
                        "ratio": hold_pct
                    })

                    # 计算预估涨幅
                    # if stock_pct_chg == '-':
                    #     print(f"{fund_name} 数据不全，可能未开盘")
                    #     continue
                    try:
                        hold_pct_float = float(hold_pct.replace("%", ""))
                    #     stock_pct_chg_float = float(stock_pct_chg.replace("%", ""))
                        total_holding_pct += hold_pct_float
                    #     est_fund_increase_pct += hold_pct_float * stock_pct_chg_float
                    except ValueError:
                        continue

            return {
                "code": fund_code,
                "name": fund_name,
                "holdings": holdings,
                "total_holding_pct": np.round(total_holding_pct,3)
            }
        except TimeoutException:
            print(f"[{fund_code}] 等待持仓表格数据超时，可能表格为空或加载失败，跳过")
            return {
                "code": fund_code,
                "name": fund_name,
                "holdings": [],
                "total_holding_pct": 0
            }

    except Exception as e:
        print(f"[{fund_code}] 持仓爬取失败：{str(e)}")
        return {
            "code": fund_code,
            "name": '',
            "holdings": {},
            "total_holding_pct": 0
        }
