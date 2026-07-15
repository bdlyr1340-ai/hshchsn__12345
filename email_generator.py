import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# تفعيل السجلات
logging.basicConfig(level=logging.INFO)

# إعدادات من متغيرات البيئة
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))
EMAIL_DOMAIN = os.getenv("EMAIL_DOMAIN", "usmail.my.id")

def create_temp_email():
    """ينشئ إيميلاً مؤقتاً من usmail.my.id."""
    options = Options()
    if BROWSER_HEADLESS:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # استخدام webdriver-manager لتثبيت chromedriver تلقائياً
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(f"https://{EMAIL_DOMAIN}/room/master")
        time.sleep(3)
        
        # استخراج الإيميل العشوائي الذي تم إنشاؤه
        email_element = WebDriverWait(driver, EMAIL_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "email-display"))
        )
        email = email_element.text
        
        logging.info(f"تم إنشاء الإيميل المؤقت: {email}")
        return email
    except Exception as e:
        logging.error(f"خطأ في إنشاء الإيميل: {str(e)}")
        return None
    finally:
        driver.quit()
