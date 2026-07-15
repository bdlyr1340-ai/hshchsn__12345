from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from config import BROWSER_HEADLESS, EMAIL_TIMEOUT, EMAIL_DOMAIN

def create_temp_email():
    options = Options()
    if BROWSER_HEADLESS:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(f"https://{EMAIL_DOMAIN}/room/master")
        time.sleep(3)
        
        # استخراج الإيميل العشوائي الذي تم إنشاؤه
        email_element = WebDriverWait(driver, EMAIL_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "email-display"))
        )
        email = email_element.text
        
        return email
    except Exception as e:
        print(f"خطأ في إنشاء الإيميل: {str(e)}")
        return None
    finally:
        driver.quit()
