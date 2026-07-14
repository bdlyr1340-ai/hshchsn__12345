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
        "👋 أهلاً بك يا صديقي في بوت Netflix الذكي لتسجيل الحسابات المباشر!\n\n"
        "💾 تم تثبيت الكوكيز الأساسية بنجاح داخل النظام.\n"
        "📧 يرجى إرسال **البريد الإلكتروني** الذي تريد تفعيل العرض/التسجيل عليه الآن للبدء."
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
        bot.send_message(chat_id, "❌ خطأ داخلي: لم يتم العثور على ملف `cookies.json` في السيرفر! يرجى التأكد من رفعه على GitHub.")
        return
    except Exception as e:
        bot.send_message(chat_id, f"❌ فشل قراءة ملف الكوكيز الداخلي:\n`{str(e)}`", parse_mode="Markdown")
        return

    status_msg = bot.send_message(chat_id, f"⏳ جاري فتح المتصفح المتخفي وحقن الكوكيز لإكمال التسجيل لـ: `{email}`...", parse_mode="Markdown")

    try:
        with sync_playwright() as p:
            # تشغيل متصفح خفي
            browser = p.firefox.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
                viewport={"width": 1280, "height": 720}
            )
            
            # تهيئة وحقن الكوكيز الخاصة بك في المتصفح
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
            
            # التوجه مباشرة لصفحة التسجيل المستهدفة بالكوكيز
            page.goto("https://www.netflix.com/signup", timeout=60000, wait_until="load")
            
            # فحص إذا كان هناك حقل إدخال بريد إلكتروني لإدخاله تلقائياً
            email_input_selector = "input[type='email'], input[name='email'], #id_email"
            
            # الانتظار لرؤية الحقل أو تجاوزه إذا كان مسجلاً بالفعل
            try:
                page.wait_for_selector(email_input_selector, timeout=10000)
                # ملء البريد الإلكتروني الذي أرسلته
                page.fill(email_input_selector, email)
                
                # البحث عن زر الاستمرار/المتابعة والضغط عليه
                submit_button_selector = "button[type='submit'], button[data-uia='action-submit-gplay']"
                if page.locator(submit_button_selector).count() > 0:
                    page.click(submit_button_selector)
                    page.wait_for_timeout(5000)  # الانتظار قليلاً ليتم معالجة الطلب والتوجيه
                
                # توليد رابط الخطوة الحالية بعد ملء الإيميل
                current_url = page.url
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text=f"🎯 **تم إدخال البريد الإلكتروني ومتابعة العملية تلقائياً!**\n\n📧 البريد: `{email}`\n🔗 رابط الجلسة المباشر لاستكمال الخطوات:\n{current_url}\n\nتم تجاوز شاشة البداية بنجاح باستخدام الكوكيز الداخلية الخاصة بك.",
                    parse_mode="Markdown"
                )
                
            except Exception as e_inner:
                # في حال لم يجد حقل الإيميل (قد يكون قد انتقل مباشرة لصفحة تالية بفضل الكوكيز)
                current_url = page.url
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text=f"ℹ️ تم الدخول للجلسة مباشرة دون الحاجة لملء الإيميل (أو لم يتم العثور على الحقل الحالي):\n\n🔗 الرابط المباشر:\n{current_url}",
                    parse_mode="Markdown"
                )
                
            browser.close()
                
    except Exception as e:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text=f"❌ حدث خطأ أثناء تشغيل المتصفح التلقائي:\n`{str(e)}`",
            parse_mode="Markdown"
        )
    finally:
        # إبقاء حالة المستخدم جاهزة لإدخال إيميل جديد
        user_data[chat_id] = {'state': STATE_WAITING_FOR_EMAIL}

# تشغيل البوت باستمرار
bot.infinity_polling()
