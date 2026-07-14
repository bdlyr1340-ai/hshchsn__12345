import os
import json
import telebot
from playwright.sync_api import sync_playwright

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# إعداد الحالة
user_data = {}
STATE_WAITING_FOR_EMAIL = "WAITING_FOR_EMAIL"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'state': STATE_WAITING_FOR_EMAIL}
    bot.send_message(chat_id, "أهلاً بك! أرسل الإيميل الآن لإنشاء الحساب الجديد باستخدام كوكيز العرض المجاني.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == STATE_WAITING_FOR_EMAIL)
def handle_email(message):
    chat_id = message.chat.id
    email = message.text.strip()
    status_msg = bot.send_message(chat_id, "جاري بدء عملية إنشاء الحساب وتطبيق العرض...")

    try:
        with open("cookies.json", "r") as f:
            cookies = json.load(f)

        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            context = browser.new_context()
            context.add_cookies(cookies)
            page = context.new_page()

            # التوجه لصفحة التسجيل مباشرة
            page.goto("https://www.netflix.com/signup/registration", timeout=60000)
            
            # انتظار ظهور حقل الإيميل وملئه
            # نستخدم محددات دقيقة لخانة الإيميل في صفحة التسجيل
            page.wait_for_selector("input[name='email']", timeout=15000)
            page.fill("input[name='email']", email)
            
            # الضغط على زر المتابعة
            page.click("button[data-uia='registration-button']")
            
            # انتظار التوجيه للخطوة التالية (تأكيد أن الإيميل قُبل)
            page.wait_for_timeout(5000)
            
            current_url = page.url
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text=f"✅ تمت العملية!\n📧 الإيميل: {email}\n🔗 رابط الاستكمال المباشر:\n{current_url}\n\nالحساب الآن جاهز لإكمال بياناته والحصول على العرض."
            )
            browser.close()

    except Exception as e:
        bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text=f"خطأ: {str(e)}")

bot.infinity_polling()
