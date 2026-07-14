import asyncio
import json
import os
import re
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from camoufox.async_api import AsyncCamoufox

# تحميل الكوكيز
with open('cookies.json', 'r') as f:
    NETFLIX_COOKIES = json.load(f)

# تحويل sameSite لصيغة Playwright
SAMESITE_MAP = {
    'strict': 'Strict',
    'lax': 'Lax',
    'no_restriction': 'None',
    'none': 'None',
    None: 'Lax',
    'unspecified': 'Lax',
    '': 'Lax'
}

def prepare_cookies(raw_cookies):
    cookies = []
    for c in raw_cookies:
        cookie = {
            'name': c['name'],
            'value': c['value'],
            'domain': c.get('domain', '.netflix.com'),
            'path': c.get('path', '/'),
            'expires': c.get('expirationDate'),
            'httpOnly': c.get('httpOnly', False),
            'secure': c.get('secure', False),
            'sameSite': SAMESITE_MAP.get(str(c.get('sameSite') or '').lower(), 'Lax')
        }
        cookies.append(cookie)
    return cookies

PLAYWRIGHT_COOKIES = prepare_cookies(NETFLIX_COOKIES)

TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN غير موجود")

browser = None
camoufox_cm = None  # نحتفظ بالمتصفح حتى نكدر نسده براحتنا
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! أرسل لي البريد الإلكتروني الذي تريد إنشاء جلسة Netflix له.")

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if not is_valid_email(email):
        await update.message.reply_text("يرجى إرسال بريد إلكتروني صالح.")
        return
    await update.message.reply_text(f"جاري معالجة البريد: {email}...")
    try:
        # نمرر الـ Bot Instance هنا حتى يدزلك لقطة شاشة إذا فشلت العملية
        link = await create_netflix_session(email, context.bot)
        await update.message.reply_text(f"تم إنشاء الجلسة! رابط الدخول:\n{link}")
    except Exception as e:
        logger.exception("فشل إنشاء الجلسة")
        await update.message.reply_text("حدث خطأ أثناء إنشاء الجلسة، حاول مجدداً لاحقاً.")

async def create_netflix_session(email, bot_instance=None):
    context = await browser.new_context()
    await context.add_cookies(PLAYWRIGHT_COOKIES)
    page = await context.new_page()
    try:
        profile_name = email.split('@')[0]
        await page.goto('https://www.netflix.com/ManageProfiles', wait_until='networkidle')
        
        # إذا تحولنا لصفحة الدخول، معناها الكوكيز انتهت صلاحيتها أو تطردت
        if "login" in page.url:
            raise Exception("الكوكيز غير صالحة - تم تحويل المتصفح لصفحة تسجيل الدخول.")
        
        add_profile_btn = page.get_by_role('link', name='Add Profile')
        if not await add_profile_btn.is_visible():
            add_profile_btn = page.get_by_text('Add Profile')
        await add_profile_btn.click()
        await page.wait_for_load_state('networkidle')

        name_input = page.locator('input[name="profileName"]')
        await name_input.fill(profile_name)
        save_btn = page.get_by_role('button', name='Save')
        if not await save_btn.is_visible():
            save_btn = page.get_by_text('Save')
        await save_btn.click()
        await page.wait_for_load_state('networkidle')

        await page.goto('https://www.netflix.com/account', wait_until='networkidle')
        get_link_btn = page.get_by_text('Get a sign-in link')
        if not await get_link_btn.is_visible():
            get_link_btn = page.locator('button:has-text("Get a sign-in link")')
        await get_link_btn.click()

        link_input = page.locator('#signin-link-input')
        await link_input.wait_for(state='visible', timeout=10000)
        signin_link = await link_input.input_value()
        if not signin_link or not signin_link.startswith('http'):
            raise Exception("لم يتم العثور على رابط الدخول المباشر.")
        return signin_link
        
    except Exception as e:
        # الميزة الأسطورية: التقاط صورة وإرسالها للمطور عند حدوث خطأ
        try:
            screenshot_path = "error_screenshot.png"
            await page.screenshot(path=screenshot_path)
            admin_id = os.environ.get('ADMIN_ID')
            if admin_id and bot_instance:
                with open(screenshot_path, 'rb') as photo:
                    await bot_instance.send_photo(
                        chat_id=admin_id,
                        photo=photo,
                        caption=f"❌ **فشلت عملية إنشاء الجلسة!**\n\n**الإيميل المطلوب:** `{email}`\n**نوع الخطأ:** `{str(e)}`"
                    )
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception as screenshot_err:
            logger.error(f"فشل التقاط لقطة الشاشة: {screenshot_err}")
        raise e
    finally:
        await context.close()

async def post_init(app: Application):
    global browser, camoufox_cm
    camoufox_cm = AsyncCamoufox(headless=True)
    browser = await camoufox_cm.__aenter__()
    logger.info("Camoufox يعمل الآن بنجاح")

async def post_shutdown(app: Application):
    global camoufox_cm
    if camoufox_cm:
        await camoufox_cm.__aexit__(None, None, None)
        logger.info("المتصفح أغلق")

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).post_shutdown(post_shutdown).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))

    webhook_url = os.environ.get('WEBHOOK_URL')
    if webhook_url:
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get('PORT', 8443)),
            webhook_url=webhook_url
        )
    else:
        app.run_polling()

if __name__ == '__main__':
    main()
