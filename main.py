import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from netflix_login import login_netflix_with_cookies

# إعدادات السجلات
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# المتغيرات المؤقتة
USER_COOKIES = {}
USER_EMAILS = {}
COOKIE_STEP, EMAIL_STEP = range(2)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "أهلاً بك.\n"
        "أرسل ملف الكوكيز الخاص بـ Netflix بصيغة JSON.\n"
        "مثال:\n```json\n[{\"domain\":\".netflix.com\",\"name\":\"NetflixId\",\"value\":\"...\"}]\n```"
    )
    return COOKIE_STEP

async def receive_cookies(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text
    
    try:
        import json
        json.loads(text)
        USER_COOKIES[user_id] = text
        await update.message.reply_text("تم استلام الكوكيز. الآن، أرسل الإيميل المطلوب:")
        return EMAIL_STEP
    except json.JSONDecodeError:
        await update.message.reply_text("خطأ: الكوكيز غير صالحة، أعد المحاولة.")
        return COOKIE_STEP

async def receive_email(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    email = update.message.text
    
    if user_id not in USER_COOKIES:
        await update.message.reply_text("لم تستلم كوكيز بعد.")
        return COOKIE_STEP
    
    USER_EMAILS[user_id] = email
    await update.message.reply_text("جاري تسجيل الدخول، يرجى الانتظار... ⏳")
    
    # تشغيل وظيفة تسجيل الدخول
    result = await login_netflix_with_cookies(USER_COOKIES[user_id])
    
    del USER_COOKIES[user_id]
    del USER_EMAILS[user_id]
    
    if result["status"] == "success":
        await update.message.reply_text(
            f"✅ اكتمل بنجاح!\n"
            f"🔗 رابط الجلسة: {result['session_url']}"
        )
    else:
        await update.message.reply_text(f"❌ فشل: {result['message']}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

def main():
    # قراءة التوكن من متغيرات البيئة في Railway
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # التوقف عن العمل إذا لم يتم العثور على التوكن
    if not TOKEN:
        print("⛔ خطأ فادح: لم يتم العثور على التوكن (TELEGRAM_BOT_TOKEN) في متغيرات البيئة!")
        return
        
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            COOKIE_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_cookies)],
            EMAIL_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(conv_handler)
    print("✅ البوت يعمل وينتظر الاتصالات...")
    app.run_polling()

if __name__ == "__main__":
    main()
