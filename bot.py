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
    bot.send_message(chat_id, "أهلاً بك! أرسل الإيميل الآن لإنشاء الحساب.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == STATE_WAITING_FOR_EMAIL)
def handle_email(message):
    chat_id = message.chat.id
    email = message.text.strip()
    status_msg = bot.send_message(chat_id, "⏳ جاري تشغيل المتصفح، يرجى الانتظار (قد يستغرق 30 ثانية)...")

    try:
        with open("cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)

        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            context = browser.new_context()

            # معالجة الكوكيز
            formatted_cookies = []
            for c in cookies:
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

            # التوجه لصفحة التسجيل مع الانتظار لاستقرار الشبكة
            page.goto("https://www.netflix.com/signup/registration", timeout=60000, wait_until="networkidle")
            
            # محاولة العثور على حقل الإيميل (أكثر من احتمال)
            selector = "input[name='email'], input[type='email'], [data-uia='field-email']"
            page.wait_for_selector(selector, timeout=60000)
            page.fill(selector, email)
            
            # الضغط على زر المتابعة
            button_selector = "button[data-uia='registration-button'], button[type='submit']"
            page.click(button_selector)
            
            # انتظار انتهاء المعالجة
            page.wait_for_timeout(10000)
            
            current_url = page.url
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text=f"✅ تم الإدخال بنجاح!\n📧 الإيميل: `{email}`\n🔗 الرابط المباشر للمتابعة:\n{current_url}",
                parse_mode="Markdown"
            )
            browser.close()

    except Exception as e:
        bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text=f"❌ خطأ: لم يتم العثور على الحقول (قد يكون هناك حماية). جرب مرة أخرى أو تأكد من الصفحة.\nالخطأ: {str(e)}")

if __name__ == "__main__":
    bot.infinity_polling()
