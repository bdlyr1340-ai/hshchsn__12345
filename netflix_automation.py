import os
import time
import random
import string
import logging

# استدعاء Camoufox الخاص بيك
from camoufox.selenium import KeepAliveWebDriver 

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from email_generator import create_temp_email

# تفعيل السجلات
logging.basicConfig(level=logging.INFO)

# إعدادات من متغيرات البيئة
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "10"))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "10"))
NETFLIX_URL = os.getenv("NETFLIX_URL", "https://www.netflix.com/")
CLEAR_COOKIES_URL = os.getenv("CLEAR_COOKIES_URL", "http://netflix.com/clearcookies")

def get_netflix_30day_offer():
    """يحاول الحصول على عرض Netflix لمدة 30 يوم وإنشاء حساب."""
    
    # إعدادات Camoufox
    options = {
        "headless": BROWSER_HEADLESS, # ياخذ القيمة من المتغيرات حتى يشتغل مخفي بالسيرفر
        "block_images": True, # لتسريع التصفح
    }
    
    attempt = 0
    
    # تشغيل متصفح Camoufox
    with KeepAliveWebDriver(**options) as driver:
        while attempt < MAX_ATTEMPTS:
            try:
                # مسح الكوكيز
                driver.get(CLEAR_COOKIES_URL)
                time.sleep(2)
                
                # تعيين كوكيز محددة للعرض 30 يوم
                driver.add_cookie({
                    "name": "nfvdid",
                    "value": "BQFmAAEBEE9JRlMuhcd1vZeyOZDGNsBgwt3MrI_af3LayzVVer6glzJvVpf97z33DXpKHBq9u0DnX0WJv5EuD1xSVUtIk9HEqcup0dtQ_aPOeD1ClWFBbYusKTD2yuO_aWV8_hyzEbgC_UGa_bLVoE2bGHdkptD2",
                    "domain": ".netflix.com"
                })
                
                # زيارة صفحة Netflix الرئيسية
                driver.get(NETFLIX_URL)
                time.sleep(3)
                
                # التحقق من وجود عرض 30 يوم
                if "30 يوم" in driver.page_source or "30 day" in driver.page_source.lower():
                    logging.info("تم العثور على عرض 30 يوم!")
                    # إنشاء إيميل وهمي
                    email = create_temp_email()
                    
                    if email:
                        # إكمال عملية التسجيل
                        password = complete_netflix_signup(driver, email)
                        
                        if password:
                            return {"email": email, "password": password}
                
                attempt += 1
                logging.info(f"المحاولة {attempt}/{MAX_ATTEMPTS} - لم يتم العثور على عرض 30 يوم، إعادة المحاولة...")
                time.sleep(5)
                
            except Exception as e:
                logging.error(f"خطأ في المحاولة {attempt}: {str(e)}")
                attempt += 1
                time.sleep(5)
                
    # بمجرد انتهاء المحاولات، الـ with راح تغلق المتصفح تلقائياً
    return None

def complete_netflix_signup(driver, email):
    """يُكمل عملية تسجيل حساب Netflix."""
    try:
        # البحث عن حقل الإيميل وإدخاله
        email_field = WebDriverWait(driver, BROWSER_TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "id_emailHero"))
        )
        email_field.send_keys(email)
        
        # النقر على زر المتابعة
        continue_button = driver.find_element(By.XPATH, "//button[contains(text(), 'متابعة') or contains(text(), 'Continue')]")
        continue_button.click()
        time.sleep(3)
        
        # التحقق من طلب كلمة المرور
        if "password" in driver.current_url.lower() or "كلمة السر" in driver.page_source:
            # إنشاء كلمة مرور عشوائية
            password = generate_random_password()
            
            # إدخال كلمة المرور
            password_field = WebDriverWait(driver, BROWSER_TIMEOUT).until(
                EC.element_to_be_clickable((By.ID, "id_password"))
            )
            password_field.send_keys(password)
            
            # إكمال التسجيل
            submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'بدء') or contains(text(), 'Start') or contains(text(), 'إكمال') or contains(text(), 'Complete')]")
            submit_button.click()
            time.sleep(5)
            
            return password
        
        return None
    except Exception as e:
        logging.error(f"خطأ في إكمال التسجيل: {str(e)}")
        return None

def generate_random_password(length=12):
    """ينشئ كلمة مرور عشوائية."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for _ in range(length))
