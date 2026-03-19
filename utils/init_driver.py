from selenium import webdriver
from selenium.webdriver.safari.options import Options
from selenium.webdriver.chrome.options import Options as ChromeOptions  # 新增：适配云函数Chrome

driver = None  # 在全局作用域先定义
# ==================== 初始化驱动（兼容Safari/Chrome，主文件控制） ====================
def init_driver(browser_type="safari", headless=True):
    """
    初始化浏览器驱动
    :param browser_type: safari/chrome，本地用safari，云函数用chrome
    :param headless: 是否无头模式（本地调试可设为False）
    :return: 初始化后的driver
    """
    global driver
    if driver is None:
        if browser_type == "safari":
            safari_options = Options()
            if headless:
                safari_options.add_argument("--headless")
            safari_options.set_capability("safari:automaticInspection", False)
            safari_options.set_capability("safari:automaticProfiling", False)
            driver = webdriver.Safari(options=safari_options)
        elif browser_type == "chrome":
            # 适配腾讯云函数的Chrome无头模式
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=chrome_options)

        # 统一设置超时
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
    return driver