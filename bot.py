import os
import json
import telebot
from playwright.sync_api import sync_playwright

# إعداد البوت
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# إعدادات الحالة
user_data = {}
STATE_WAITING_FOR_EMAIL = "WAITING_FOR_EMAIL"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'state': STATE_WAITING_FOR_EMAIL}
    bot.send_message(chat_id, "مرحباً! أرسل الإيميل الآن لإنشاء الحساب باستخدام كوكيز العرض المجاني.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == STATE_WAITING_FOR_EMAIL)
def handle_email(message):
    chat_id = message.chat.id
    email = message.text.strip()
    status_msg = bot.send_message(chat_id, "⏳ جاري المعالجة... يرجى الانتظار.")

    try:
        # قراءة الكوكيز
        with open("cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)

        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            context = browser.new_context()

            # تنظيف وتجهيز الكوكيز (مع حل مشكلة SameSite)
            formatted_cookies = []
            for c in cookies:
                # تصحيح قيمة sameSite
                samesite = c.get("sameSite")
                if samesite not in ["Strict", "Lax", "None"]:
                    samesite = "Lax"
                
                formatted_cookies.append({
                    "name": c.get("name"),
                    "value": c.get("value"),
                    "domain": c.get("domain", ".netflix.com"),
                    "path": c.get("path", "/"),
                    "secure": c.get("secure", True),
                    "httpOnly": c.get("httpOnly", False),
                    "sameSite": samesite
                })
            
            context.add_cookies(formatted_cookies)
            page = context.new_page()

            # التوجه لصفحة التسجيل
            page.goto("https://www.netflix.com/signup/registration", timeout=60000)
            
            # إدخال الإيميل
            page.wait_for_selector("input[name='email']", timeout=15000)
            page.fill("input[name='email']", email)
            
            # الضغط على زر المتابعة
            page.click("button[data-uia='registration-button']")
            
            # انتظار التحميل
            page.wait_for_timeout(5000)
            
            current_url = page.url
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text=f"✅ تمت العملية بنجاح!\n📧 الإيميل: `{email}`\n🔗 الرابط الحالي: {current_url}\n\nتم تجاوز الخطوة الأولى بنجاح.",
                parse_mode="Markdown"
            )
            browser.close()

    except Exception as e:
        bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text=f"❌ خطأ تقني: {str(e)}")

# تشغيل البوت
if __name__ == "__main__":
    bot.infinity_polling()
