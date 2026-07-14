import os
import json
import telebot
from playwright.sync_api import sync_playwright

# جلب توكن البوت
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# قاموس لتتبع حالة المستخدمين
user_data = {}
STATE_WAITING_FOR_EMAIL = "WAITING_FOR_EMAIL"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'state': STATE_WAITING_FOR_EMAIL}
    
    welcome_text = (
        "👋 أهلاً بك يا صديقي في بوت Netflix الذكي!\n\n"
        "💾 تم تحميل ملف الكوكيز الداخلي بنجاح.\n"
        "📧 يرجى الآن إرسال **البريد الإلكتروني** لحساب Netflix للبدء في فحص وتسجيل الدخول المباشر."
    )
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == STATE_WAITING_FOR_EMAIL)
def handle_email(message):
    chat_id = message.chat.id
    email = message.text.strip()
    
    # قراءة الكوكيز من الملف الداخلي cookies.json
    try:
        with open("cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)
    except FileNotFoundError:
        bot.send_message(chat_id, "❌ خطأ داخلي: لم يتم العثور على ملف `cookies.json` في السيرفر! يرجى رفعه أولاً.")
        return
    except Exception as e:
        bot.send_message(chat_id, f"❌ فشل قراءة ملف الكوكيز الداخلي. تأكد من صيغته.\nالخطأ: `{str(e)}`", parse_mode="Markdown")
        return

    status_msg = bot.send_message(chat_id, f"⏳ جاري فحص الحساب واستخدام الكوكيز الداخلية لـ: `{email}`...", parse_mode="Markdown")

    try:
        with sync_playwright() as p:
            # تشغيل متصفح خفي
            browser = p.firefox.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
                viewport={"width": 1280, "height": 720}
            )
            
            # تهيئة الكوكيز الداخلية لتناسب المتصفح
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
            
            # التوجه لـ Netflix
            page.goto("https://www.netflix.com/YourAccount", timeout=60000, wait_until="load")
            
            current_url = page.url
            if "YourAccount" in current_url or "browse" in current_url:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text=f"🎉 **اكتمل تسجيل الدخول بنجاح!**\n\n📧 الحساب: `{email}`\n🌐 رابط الجلسة النشط: {current_url}\n\nتم التحقق بنجاح والجلسة الآن فعالة.",
                    parse_mode="Markdown"
                )
            else:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text="⚠️ فشل تسجيل الدخول. يبدو أن الكوكيز المحفوظة داخلياً قد انتهت صلاحيتها أو غير صالحة."
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
        # إبقاء البوت جاهزاً للطلب التالي
        user_data[chat_id] = {'state': STATE_WAITING_FOR_EMAIL}

# تشغيل مستمر ومقاوم للأعطال المفاجئة
bot.infinity_polling()
