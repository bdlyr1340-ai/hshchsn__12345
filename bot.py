import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from netflix_automation import get_netflix_30day_offer

# تفعيل السجلات لتتبع الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# قراءة التوكن من متغير البيئة
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN:
    raise ValueError("لم يتم العثور على متغير TELEGRAM_BOT_TOKEN. تأكد من إضافته في Railway Variables.")

def start(update: Update, context: CallbackContext):
    """يرسل رسالة ترحيب عند استخدام أمر /start."""
    update.message.reply_text("مرحباً! بوت Netflix جاهز للعمل. أرسل /create_netflix لإنشاء حساب جديد")

def create_netflix(update: Update, context: CallbackContext):
    """ينشئ حساب Netflix جديد بعرض 30 يوم."""
    update.message.reply_text("جاري إنشاء حساب Netflix... قد يستغرق هذا بعض الوقت، يرجى الانتظار.")
    
    netflix_account = get_netflix_30day_offer()
    
    if netflix_account:
        message = f"✅ تم إنشاء الحساب بنجاح!\n\n📧 الإيميل: {netflix_account['email']}\n🔑 الباسورد: {netflix_account['password']}"
        update.message.reply_text(message)
        
        # إرسال نسخة إلى الأدمن إذا تم تحديده
        if ADMIN_ID:
            try:
                context.bot.send_message(chat_id=ADMIN_ID, text=f"حساب جديد تم إنشاؤه:\n\n{message}")
            except Exception as e:
                logging.error(f"فشل إرسال رسالة إلى الأدمن: {str(e)}")
    else:
        update.message.reply_text("❌ فشل في إنشاء الحساب، يرجى المحاولة مرة أخرى لاحقاً.")

def main():
    """بدء تشغيل البوت."""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("create_netflix", create_netflix))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
