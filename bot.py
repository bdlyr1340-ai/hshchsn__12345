from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import string

# إعدادات البوت
TOKEN = "YOUR_BOT_TOKEN"

# وظيفة لبدء البوت
def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحباً! بوت Netflix جاهز للعمل. أرسل /create_netflix لإنشاء حساب جديد")

# وظيفة إنشاء حساب Netflix
def create_netflix(update: Update, context: CallbackContext):
    update.message.reply_text("جاري إنشاء حساب Netflix... قد يستغرق هذا بعض الوقت")
    
    # الخطوة 1: مسح الكوكيز والمحاولة للحصول على عرض 30 يوم
    netflix_account = get_netflix_30day_offer()
    
    if netflix_account:
        update.message.reply_text(f"تم إنشاء الحساب بنجاح!\nالإيميل: {netflix_account['email']}\nالباسورد: {netflix_account['password']}")
    else:
        update.message.reply_text("فشل في إنشاء الحساب، يرجى المحاولة مرة أخرى لاحقاً")

def get_netflix_30day_offer():
    # استخدام Camoufox أو متصفح مشابه
    options = webdriver.ChromeOptions()
    # إعدادات Camoufox هنا
    
    driver = webdriver.Chrome(options=options)
    
    max_attempts = 10
    attempt = 0
    
    while attempt < max_attempts:
        try:
            # مسح الكوكيز
            driver.get("http://netflix.com/clearcookies")
            time.sleep(2)
            
            # تعيين كوكيز محددة للعرض 30 يوم
            driver.add_cookie({
                "name": "nfvdid",
                "value": "BQFmAAEBEE9JRlMuhcd1vZeyOZDGNsBgwt3MrI_af3LayzVVer6glzJvVpf97z33DXpKHBq9u0DnX0WJv5EuD1xSVUtIk9HEqcup0dtQ_aPOeD1ClWFBbYusKTD2yuO_aWV8_hyzEbgC_UGa_bLVoE2bGHdkptD2",
                "domain": ".netflix.com"
            })
            
            # زيارة صفحة Netflix الرئيسية
            driver.get("https://www.netflix.com/")
            time.sleep(3)
            
            # التحقق من وجود عرض 30 يوم
            if "30 يوم" in driver.page_source or "30 day" in driver.page_source.lower():
                # إنشاء إيميل وهمي
                email = create_temp_email()
                
                if email:
                    # إكمال عملية التسجيل
                    password = complete_netflix_signup(driver, email)
                    
                    if password:
                        return {"email": email, "password": password}
            
            attempt += 1
            time.sleep(5)
            
        except Exception as e:
            print(f"خطأ في المحاولة {attempt}: {str(e)}")
            attempt += 1
            time.sleep(5)
    
    driver.quit()
    return None

def create_temp_email():
    driver = webdriver.Chrome()
    try:
        driver.get("https://usmail.my.id/room/master")
        time.sleep(3)
        
        # استخراج الإيميل العشوائي الذي تم إنشاؤه
        email_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "email-display"))
        )
        email = email_element.text
        
        return email
    except Exception as e:
        print(f"خطأ في إنشاء الإيميل: {str(e)}")
        return None
    finally:
        driver.quit()

def complete_netflix_signup(driver, email):
    try:
        # البحث عن حقل الإيميل وإدخاله
        email_field = WebDriverWait(driver, 10).until(
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
            password_field = WebDriverWait(driver, 10).until(
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
        print(f"خطأ في إكمال التسجيل: {str(e)}")
        return None

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for _ in range(length))

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("create_netflix", create_netflix))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
