from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from netflix_automation import get_netflix_30day_offer
from config import TOKEN

# وظيفة لبدء البوت
def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحباً! بوت Netflix جاهز للعمل. أرسل /create_netflix لإنشاء حساب جديد")

# وظيفة إنشاء حساب Netflix
def create_netflix(update: Update, context: CallbackContext):
    update.message.reply_text("جاري إنشاء حساب Netflix... قد يستغرق هذا بعض الوقت")
    
    netflix_account = get_netflix_30day_offer()
    
    if netflix_account:
        update.message.reply_text(f"تم إنشاء الحساب بنجاح!\nالإيميل: {netflix_account['email']}\nالباسورد: {netflix_account['password']}")
    else:
        update.message.reply_text("فشل في إنشاء الحساب، يرجى المحاولة مرة أخرى لاحقاً")

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("create_netflix", create_netflix))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
