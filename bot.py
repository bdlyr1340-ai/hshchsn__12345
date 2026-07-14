import os
import json
import telebot
from playwright.sync_api import sync_playwright

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

user_data = {}
STATE_WAITING_FOR_EMAIL = "WAITING_FOR_EMAIL"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'state': STATE_WAITING_FOR_EMAIL}
    bot.send_message(chat_id, "أهلاً بك! أرسل الإيميل الآن للبدء.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == STATE_WAITING_FOR_EMAIL)
def handle_email(message):
    chat_id = message.chat.id
    email = message.text.strip()
    status_msg = bot.send_message(chat_id, "⏳ جاري المعالجة...")

    try:
        with open("cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)

        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
            )
            
            # معالجة الكوكيز
            formatted_cookies = []
            for c in cookies:
                formatted_cookies.append({
                    "name": c.get("name"), "value": c.get("value"),
                    "domain": c.get("domain", ".netflix.com"),
                    "path": c.get("path", "/"),
                    "secure": c.get("secure", True),
                    "httpOnly": c.get("httpOnly", False),
                    "sameSite": c.get("sameSite") if c.get("sameSite") in ["Strict", "Lax", "None"] else "Lax"
                })
            
            context.add_cookies(formatted_cookies)
            page = context.new_page()

            # التوجه لصفحة التسجيل
            page.goto("https://www.netflix.com/signup/registration", timeout=60000)
            
            # محاولة الإدخال
            selector = "input[name='email']"
            page.wait_for_selector(selector, timeout=30000)
            page.fill(selector, email)
            page.click("button[data-uia='registration-button']")
            
            bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="✅ تمت العملية بنجاح!")
            browser.close()

    except Exception as e:
        # هنا السحر: التقاط صورة عند الفشل
        error_file = "error_screenshot.png"
        try:
            page.screenshot(path=error_file)
            with open(error_file, 'rb') as photo:
                bot.send_photo(chat_id, photo, caption=f"❌ فشل البوت! إليك لقطة الشاشة للخطأ:\n{str(e)}")
        except:
            bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text=f"❌ خطأ فادح: {str(e)}")
        
        if 'browser' in locals(): browser.close()

if __name__ == "__main__":
    bot.infinity_polling()
