import os
import json
import telebot
from playwright.sync_api import sync_playwright

# احصل على توكن البوت من بيئة التشغيل
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# قاموس لحفظ بيانات المستخدمين مؤقتاً
user_data = {}

STATE_WAITING_FOR_COOKIES = "WAITING_FOR_COOKIES"
STATE_WAITING_FOR_EMAIL = "WAITING_FOR_EMAIL"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    
    welcome_text = (
        "👋 أهلاً بك يا صديقي في بوت تسجيل دخول Netflix المطور!\n\n"
        "📥 **الخطوة الأولى:** يرجى إرسال ملف **الكوكيز (Cookies)** الخاص بالحساب بصيغة JSON."
    )
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown")
    user_data[chat_id]['state'] = STATE_WAITING_FOR_COOKIES

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == STATE_WAITING_FOR_COOKIES)
def handle_cookies(message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    try:
        # التحقق من صحة الكوكيز
        cookies = json.loads(text)
        if not isinstance(cookies, list):
            raise ValueError("يجب أن تكون الكوكيز عبارة عن قائمة JSON.")
            
        user_data[chat_id]['cookies'] = cookies
        user_data[chat_id]['state'] = STATE_WAITING_FOR_EMAIL
        
        bot.send_message(chat_id, "✅ تم حفظ الكوكيز بنجاح!\n\n📧 الآن، يرجى إرسال **الإيميل** الخاص بالحساب لتسجيل الدخول.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ صيغة الكوكيز غير صحيحة. تأكد من نسخ النص بالكامل.\nالخطأ: {str(e)}")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == STATE_WAITING_FOR_EMAIL)
def handle_email(message):
    chat_id = message.chat.id
    email = message.text.strip()
    
    cookies = user_data[chat_id].get('cookies')
    if not cookies:
        bot.send_message(chat_id, "❌ حدث خطأ، يرجى إرسال /start للبدء من جديد.")
        return

    status_msg = bot.send_message(chat_id, "⏳ جاري تشغيل المتصفح الآمن وفحص الحساب...")

    try:
        with sync_playwright() as p:
            # تشغيل متصفح فايرفوكس بإعدادات تخفي ممتازة
            browser = p.firefox.launch(headless=True)
            
            # محاكاة جهاز حقيقي لتخطي أنظمة الحماية
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
                viewport={"width": 1280, "height": 720}
            )
            
            # تهيئة وتصفية الكوكيز
            formatted_cookies = []
            for c in cookies:
                formatted_cookies.append({
                    "name": c.get("name"),
                    "value": c.get("value"),
                    "domain": c.get("domain") if c.get("domain").startswith(".") else f".{c.get('domain')}",
                    "path": c.get("path", "/"),
                    "secure": c.get("secure", True),
                    "httpOnly": c.get("httpOnly", False)
                })
            
            context.add_cookies(formatted_cookies)
            page = context.new_page()
            
            # الدخول لـ Netflix
            page.goto("https://www.netflix.com/YourAccount", timeout=60000, wait_until="load")
            
            current_url = page.url
            if "YourAccount" in current_url or "browse" in current_url:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text=f"🎉 **اكتمل تسجيل الدخول بنجاح!**\n\n📧 الحساب: `{email}`\n🌐 رابط الجلسة النشط: {current_url}\n\nجاهز للاستخدام الآن.",
                    parse_mode="Markdown"
                )
            else:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text="⚠️ فشل تسجيل الدخول. قد تكون الكوكيز قديمة أو غير صالحة."
                )
            browser.close()
                
    except Exception as e:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text=f"❌ حدث خطأ أثناء الاتصال بالخادم:\n`{str(e)}`",
            parse_mode="Markdown"
        )
    finally:
        user_data[chat_id] = {}

# بدء تشغيل البوت واستقبال الرسائل بشكل مستمر
bot.infinity_polling()
