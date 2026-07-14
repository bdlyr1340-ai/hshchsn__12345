import os
import json
import telebot
from telebot import types
from camoufox.sync_api import Camoufox

# احصل على توكن البوت من بيئة التشغيل (سيتم ضبطه في Railway)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# قاموس لحفظ بيانات المستخدمين مؤقتاً أثناء المحادثة
user_data = {}

# حالات المستخدم
STATE_WAITING_FOR_COOKIES = "WAITING_FOR_COOKIES"
STATE_WAITING_FOR_EMAIL = "WAITING_FOR_EMAIL"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    
    welcome_text = (
        "👋 أهلاً بك يا صديقي في بوت تسجيل دخول Netflix الذكي!\n\n"
        "📥 الخطوة الأولى: يرجى إرسال ملف **الكوكيز (Cookies)** الخاص بحساب Netflix بصيغة JSON."
    )
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown")
    user_data[chat_id]['state'] = STATE_WAITING_FOR_COOKIES

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == STATE_WAITING_FOR_COOKIES)
def handle_cookies(message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    try:
        # محاولة التحقق من صحة صيغة الـ JSON للكوكيز
        cookies = json.loads(text)
        if not isinstance(cookies, list):
            raise ValueError("الكوكيز يجب أن تكون على شكل قائمة (List)")
            
        user_data[chat_id]['cookies'] = cookies
        user_data[chat_id]['state'] = STATE_WAITING_FOR_EMAIL
        
        bot.send_message(chat_id, "✅ تم حفظ الكوكيز بنجاح!\n\n📧 الآن، يرجى إرسال **الإيميل** المرتبط بالحساب للبدء في عملية تسجيل الدخول.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ صيغة الكوكيز غير صحيحة. يرجى التأكد من نسخ كود JSON بالكامل وإعادة إرساله.\nالخطأ: {str(e)}")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == STATE_WAITING_FOR_EMAIL)
def handle_email(message):
    chat_id = message.chat.id
    email = message.text.strip()
    
    cookies = user_data[chat_id].get('cookies')
    if not cookies:
        bot.send_message(chat_id, "❌ حدث خطأ، لم نجد الكوكيز الخاصة بك. يرجى إرسال /start من جديد.")
        return

    status_msg = bot.send_message(chat_id, "⏳ جاري تشغيل المتصفح الآمن (Camoufox) والاتصال بـ Netflix...")

    try:
        # تشغيل متصفح Camoufox المخفي لتخطي الحماية
        with Camoufox(headless=True) as browser:
            # إنشاء سياق متصفح جديد وضبط الكوكيز داخله
            context = browser.new_context()
            
            # تعديل نطاق الكوكيز ليتناسب مع صيغة Playwright
            formatted_cookies = []
            for c in cookies:
                formatted_cookies.append({
                    "name": c.get("name"),
                    "value": c.get("value"),
                    "domain": c.get("domain"),
                    "path": c.get("path", "/"),
                    "secure": c.get("secure", True),
                    "httpOnly": c.get("httpOnly", False)
                })
            
            context.add_cookies(formatted_cookies)
            page = context.new_page()
            
            # التوجه مباشرة لصفحة الحساب في نتفلكس للتأكد من نجاح الدخول
            page.goto("https://www.netflix.com/YourAccount", wait_until="networkidle")
            
            # التحقق إذا كنا داخل الصفحة الشخصية أو تم رفض الجلسة
            current_url = page.url
            if "YourAccount" in current_url or "browse" in current_url:
                # توليد رابط الجلسة المباشر أو تأكيد النجاح
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text=f"🎉 **اكتمل تسجيل الدخول بنجاح!**\n\n📧 الحساب: `{email}`\n🌐 الرابط النشط: {current_url}\n\nتم التحقق من الجلسة وتخطي جدار الحماية بنجاح.",
                    parse_mode="Markdown"
                )
            else:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text="⚠️ فشل تسجيل الدخول المباشر. قد تكون الكوكيز منتهية الصلاحية أو غير مطابقة للحساب."
                )
                
    except Exception as e:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text=f"❌ حدث خطأ أثناء محاولة الدخول الآمن:\n`{str(e)}`",
            parse_mode="Markdown"
        )
    finally:
        # تصفير حالة المستخدم للبدء من جديد عند الحاجة
        user_data[chat_id] = {}
