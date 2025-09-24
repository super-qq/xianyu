from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time


def get_chrome_driver():
    """创建并配置Chrome浏览器驱动"""
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })

    dirver_path = "/usr/local/bin/chromedriver/chromedriver"
    service = Service(dirver_path)
    return webdriver.Chrome(options=chrome_options, service=service)


def login(driver):
    """登录闲管家系统"""
    try:
        # 打开登录页面
        driver.get("https://goofish.pro/login")
        print("已打开闲管家登录界面窗口，当前页面：", driver.title)
        time.sleep(2)
        
        # 点击"密码登录"选项
        password_login_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='tab-third']"))
        )
        password_login_option.click()
        print("已点击密码登录选项")
        time.sleep(2)
        
        # 输入账号（手机号码）
        username_input = WebDriverWait(driver, 300).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='pane-third']/form/div[1]/div/div/input"))
        )
        username_input.clear()
        username_input.send_keys("13939100292")
        print("已输入账号")
        
        # 输入密码
        password_input = driver.find_element(By.XPATH, "//*[@id='pane-third']/form/div[2]/div/div/input")
        password_input.clear()
        password_input.send_keys("ljq990807")
        print("已输入密码")
        
        # 处理验证码
        captcha_input = WebDriverWait(driver, 300).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='请输入验证码']"))
        )
        captcha_code = input("请查看浏览器中的验证码并输入: ")
        captcha_input.send_keys(captcha_code)
        print("已输入验证码")
        
        # 点击登录按钮
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@id='pane-third']//button[@type='button']"))
        )
        login_button.click()
        print("已点击登录按钮")
        
        # 等待登录结果
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='app']/section/header/div/div[2]/div/div/button"))
            )
            print("登录成功！")
            
            # 处理登录后的弹窗
            checked_button = WebDriverWait(driver,10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/section/header/div/div[2]/div/div/button"))
            )
            checked_button.click()
            print("已点击客服管家上线-知道了按钮!")
            return True
            
        except:
            print("登录可能失败，请检查输入信息或页面状态")
            return False
            
    except Exception as e:
        print(f"登录过程出错: {str(e)}")
        return False