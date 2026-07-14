import asyncio
import json
import os
import re
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import camoufox

# تحميل الكوكيز
with open('cookies.json', 'r') as f:
    NETFLIX_COOKIES = json.load(f)

# تحويل sameSite لصيغة Playwright
SAMESITE_MAP = {
    'strict': 'Strict',
    'lax': 'Lax',
    'no_restriction': 'None',
    None: 'Lax',
    'unspecified': 'Lax'
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
            'sameSite': SAMESITE_MAP.get(c.get('sameSite', '').lower(), 'Lax')
        }
        cookies.append(cookie)
    return cookies

PLAYWRIGHT_COOKIES = prepare_cookies(NETFLIX_COOKIES)

TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN غير موجود")

browser = None
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
        link = await create_netflix_session(email)
        await update.message.reply_text(f"تم إنشاء الجلسة! رابط الدخول:\n{link}")
    except Exception as e:
        logger.exception("فشل إنشاء الجلسة")
        await update.message.reply_text("حدث خطأ أثناء إنشاء الجلسة، حاول مجدداً لاحقاً.")

async def create_netflix_session(email):
    context = await browser.new_context()
    await context.add_cookies(PLAYWRIGHT_COOKIES)
    page = await context.new_page()
    try:
        # إنشاء بروفايل جديد باسم مختصر من الإيميل
        profile_name = email.split('@')[0]
        await page.goto('https://www.netflix.com/ManageProfiles', wait_until='networkidle')
        if "login" in page.url:
            raise Exception("الكوكيز غير صالحة - تم التحويل لصفحة الدخول")
        
        # الضغط على Add Profile
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

        # استخراج رابط الدخول المباشر
        await page.goto('https://www.netflix.com/account', wait_until='networkidle')
        get_link_btn = page.get_by_text('Get a sign-in link')
        if not await get_link_btn.is_visible():
            get_link_btn = page.locator('button:has-text("Get a sign-in link")')
        await get_link_btn.click()

        link_input = page.locator('#signin-link-input')
        await link_input.wait_for(state='visible', timeout=10000)
        signin_link = await link_input.input_value()
        if not signin_link or not signin_link.startswith('http'):
            raise Exception("لم يتم العثور على رابط الدخول")
        return signin_link
    finally:
        await context.close()

async def post_shutdown(app):
    global browser
    if browser:
        await browser.close()
        logger.info("المتصفح أغلق")

async def main():
    global browser
    browser = await camoufox.launch(headless=True)
    logger.info("Camoufox يعمل")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))
    app.post_shutdown = post_shutdown

    # استخدم ويبهوك إذا وُجد المتغير، وإلا استخدم بولينغ (الأسهل للنشر)
    webhook_url = os.environ.get('WEBHOOK_URL')
    if webhook_url:
        await app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get('PORT', 8443)),
            webhook_url=webhook_url
        )
    else:
        await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
