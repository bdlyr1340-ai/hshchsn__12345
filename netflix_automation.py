import os
import time
import random
import string
import logging
from camoufox.sync_api import Camoufox
from email_generator import create_temp_email

# تفعيل السجلات
logging.basicConfig(level=logging.INFO)

# إعدادات من متغيرات البيئة
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
# تحويل الثواني إلى ميلي ثانية لأن مكتبة Playwright تتعامل بالميلي ثانية
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "10")) * 1000 
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "10"))
NETFLIX_URL = os.getenv("NETFLIX_URL", "https://www.netflix.com/")
CLEAR_COOKIES_URL = os.getenv("CLEAR_COOKIES_URL", "http://netflix.com/clearcookies")

def get_netflix_30day_offer():
    """يحاول الحصول على عرض Netflix لمدة 30 يوم وإنشاء حساب."""
    attempt = 0
    
    # تشغيل متصفح Camoufox بوضعية التخفي
    with Camoufox(headless=BROWSER_HEADLESS) as browser:
        page = browser.new_page()
        
        while attempt < MAX_ATTEMPTS:
            try:
                # مسح الكوكيز
                page.goto(CLEAR_COOKIES_URL)
                time.sleep(2)
                
                # تعيين كوكيز محددة للعرض 30 يوم
                page.context.add_cookies([{
                    "name": "nfvdid",
                    "value": "BQFmAAEBEE9JRlMuhcd1vZeyOZDGNsBgwt3MrI_af3LayzVVer6glzJvVpf97z33DXpKHBq9u0DnX0WJv5EuD1xSVUtIk9HEqcup0dtQ_aPOeD1ClWFBbYusKTD2yuO_aWV8_hyzEbgC_UGa_bLVoE2bGHdkptD2",
                    "domain": ".netflix.com",
                    "path": "/"
                }])
                
                # زيارة صفحة Netflix الرئيسية
                page.goto(NETFLIX_URL)
                time.sleep(3)
                
                content = page.content()
                
                # التحقق من وجود عرض 30 يوم
                if "30 يوم" in content or "30 day" in content.lower():
                    logging.info("تم العثور على عرض 30 يوم!")
                    # إنشاء إيميل وهمي
                    email = create_temp_email()
                    
                    if email:
                        # إكمال عملية التسجيل
                        password = complete_netflix_signup(page, email)
                        
                        if password:
                            return {"email": email, "password": password}
                
                attempt += 1
                logging.info(f"المحاولة {attempt}/{MAX_ATTEMPTS} - لم يتم العثور على عرض 30 يوم، إعادة المحاولة...")
                time.sleep(5)
                
            except Exception as e:
                logging.error(f"خطأ في المحاولة {attempt}: {str(e)}")
                attempt += 1
                time.sleep(5)
                
    return None

def complete_netflix_signup(page, email):
    """يُكمل عملية تسجيل حساب Netflix."""
    try:
        # البحث عن حقل الإيميل وإدخاله
        page.wait_for_selector("#id_emailHero", timeout=BROWSER_TIMEOUT)
        page.fill("#id_emailHero", email)
        
        # النقر على زر المتابعة
        page.locator("//button[contains(text(), 'متابعة') or contains(text(), 'Continue')]").click()
        time.sleep(3)
        
        # التحقق من طلب كلمة المرور
        if "password" in page.url.lower() or "كلمة السر" in page.content():
            # إنشاء كلمة مرور عشوائية
            password = generate_random_password()
            
            # إدخال كلمة المرور
            page.wait_for_selector("#id_password", timeout=BROWSER_TIMEOUT)
            page.fill("#id_password", password)
            
            # إكمال التسجيل
            page.locator("//button[contains(text(), 'بدء') or contains(text(), 'Start') or contains(text(), 'إكمال') or contains(text(), 'Complete')]").click()
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
