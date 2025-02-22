import multiprocessing
import threading
import ddddocr
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup  # 添加BeautifulSoup库的导入
import os
import random
import string

ocr = ddddocr.DdddOcr()


def run(debug=False):
    while True:
        try:
            # 添加对反爬虫机制的处理
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument('--headless')
            # 禁用自动化扩展
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            # 移除 navigator.webdriver 标志
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            service = Service('./chromedriver.exe')
            driver = webdriver.Chrome(service=service, options=chrome_options)

            try:
                print("正在获取网页")
                driver.get('http://www.mayikt.com/login.html')
                if driver.current_url == 'http://www.mayikt.com/login.html':
                    if debug:
                        print("HTML内容已成功获取")
                    html_content = driver.page_source
                    if debug:
                        print(html_content)
                    # 查找<img src="/api/captcha">标签并下载图片
                    soup = BeautifulSoup(html_content, 'html.parser')
                    captcha_img = soup.find(src='/api/captcha')
                    if captcha_img:
                        captcha_src = captcha_img['src']
                        captcha_url = 'http://www.mayikt.com' + captcha_src
                        if debug:
                            print("Captcha image URL:", captcha_url)

                        # 下载图片
                        try:
                            # 使用driver保存图片
                            captcha_element = driver.find_element(By.XPATH, f"//img[@src='{captcha_src}']")
                            # 生成随机文件名
                            random_filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + '.png'
                            captcha_path = os.path.join('./captcha', random_filename)
                            captcha_element.screenshot(captcha_path)
                            if debug:
                                print(f"Captcha image downloaded successfully using driver: {captcha_path}")
                            ocr_result = ocr.classification(open(captcha_path, 'rb').read())
                            # 处理OCR结果
                            if not ocr_result:
                                if debug:
                                    print("OCR failed to recognize the captcha.")
                            else:
                                if debug:
                                    print("Captcha recognized successfully:", ocr_result)

                                # 生成随机电话号码
                                phone_number = ''.join(random.choices('0123456789', k=11))
                                if debug:
                                    print("Generated phone number:", phone_number)

                                # 填写电话号码和验证码
                                phone_input = driver.find_element(By.ID, 'u-email-reg')
                                phone_input.send_keys(phone_number)

                                captcha_input = driver.find_element(By.ID, 'regImageCode')
                                captcha_input.send_keys(ocr_result)

                                # 提交表单
                                submit_button = driver.find_element(By.XPATH, "//button[text()='注册/关联']")
                                # 增加显式等待，确保元素加载完成后再进行操作
                                WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, "//button[text()='注册/关联']")))
                                submit_button.click()
                                print("成功提交!")
                        except Exception as e:
                            if debug:
                                print(f"Failed to download captcha image using driver: {e}")
                    else:
                        if debug:
                            print("Captcha image not found.")
                else:
                    if debug:
                        print("Failed to get the login page.")
            except Exception as e:
                if debug:
                    print(f"An error occurred: {e}")
        except TimeoutError:
            if debug:
                print("页面加载超时")
        finally:
            driver.quit()

if __name__ == '__main__':
    debug_mode = False  # 设置debug模式
    pool = multiprocessing.Pool(processes=os.cpu_count()-1)
    for _ in range(os.cpu_count()*2):
        pool.apply_async(run, args=(debug_mode,))
    pool.close()
    pool.join()