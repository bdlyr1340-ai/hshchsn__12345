import asyncio
import json
import os
import re
import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from camoufox import Camoufox  # ✅ الاستيراد الصحيح

# -------------------- إعداد السجل --------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# -------------------- تحميل الكوكيز --------------------
with open('cookies.json', 'r') as f:
    NETFLIX_COOKIES = json.load(f)

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

# -------------------- المتغيرات --------------------
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN غير مضبوط")
    sys.exit(1)

MAX_PROFILES = 5

# -------------------- دوال البوت --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! أرسل لي البريد الإلكتروني الذي تريد إنشاء جلسة Netflix له.")

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

async def create_netflix_session(email: str, browser) -> tuple[str, bytes | None]:
    """تأخذ المتصفح كوسيط لإنشاء سياق جديد في كل مرة"""
    context = await browser.new_context()
    await context.add_cookies(PLAYWRIGHT_COOKIES)
    page = await context.new_page()
    screenshot = None
    try:
        logger.info(f"معالجة البريد: {email}")
        
        # 1. الذهاب إلى إدارة الملفات الشخصية
        await page.goto('https://www.netflix.com/ManageProfiles', wait_until='domcontentloaded')
        if "login" in page.url:
            raise Exception("الكوكيز غير صالحة - تم التحويل إلى صفحة تسجيل الدخول.")

        # 2. عد الملفات الشخصية الحالية
        profile_items = page.locator('li.profile, .profile-gate-label, [data-profile-gate]')
        current_count = await profile_items.count()
        logger.info(f"عدد الملفات الشخصية الحالية: {current_count}")
        
        if current_count >= MAX_PROFILES:
            raise Exception(f"الحساب ممتلئ ({MAX_PROFILES} ملفات شخصية). يجب حذف ملف قبل الإضافة.")

        # 3. إضافة ملف شخصي
        add_profile_btn = page.get_by_role('link', name='Add Profile')
        if not await add_profile_btn.is_visible():
            add_profile_btn = page.locator('a:has-text("Add Profile"), button:has-text("Add Profile")')
            if await add_profile_btn.count() == 0:
                await page.screenshot(path='error_add_profile.png')
                with open('error_add_profile.png', 'rb') as f:
                    screenshot = f.read()
                raise Exception("لم أتمكن من إيجاد زر إضافة ملف شخصي، راجع اللقطة.")
        await add_profile_btn.click()
        await page.wait_for_load_state('networkidle')

        # 4. تعبئة الاسم
        profile_name = email.split('@')[0][:20]
        name_input = page.locator('input[name="profileName"]')
        await name_input.fill(profile_name)

        save_btn = page.get_by_role('button', name='Save')
        if not await save_btn.is_visible():
            save_btn = page.locator('button:has-text("Save")')
        await save_btn.click()
        await page.wait_for_load_state('networkidle')

        # 5. استخراج رابط الدخول
        await page.goto('https://www.netflix.com/account', wait_until='networkidle')
        get_link_btn = page.get_by_text('Get a sign-in link')
        if not await get_link_btn.is_visible():
            get_link_btn = page.locator('button:has-text("Get a sign-in link")')
        await get_link_btn.click()

        link_input = page.locator('#signin-link-input')
        await link_input.wait_for(state='visible', timeout=10000)
        signin_link = await link_input.input_value()
        if not signin_link or not signin_link.startswith('http'):
            raise Exception("رابط الدخول فارغ أو غير صالح.")
        logger.info(f"تم إنشاء الجلسة: {signin_link[:50]}...")
        return signin_link, None

    except Exception as e:
        logger.exception("خطأ أثناء create_netflix_session")
        if screenshot is None:
            try:
                await page.screenshot(path='error_screenshot.png')
                with open('error_screenshot.png', 'rb') as f:
                    screenshot = f.read()
            except Exception as ss_err:
                logger.warning(f"تعذر التقاط لقطة: {ss_err}")
        return None, screenshot
    finally:
        await context.close()

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if not is_valid_email(email):
        await update.message.reply_text("❌ يرجى إرسال بريد إلكتروني صالح.")
        return

    browser = context.bot_data.get('browser')
    if not browser:
        await update.message.reply_text("⚠️ المتصفح غير جاهز، يرجى الانتظار قليلاً.")
        return

    wait_msg = await update.message.reply_text(f"⏳ جاري معالجة البريد: {email}...")
    try:
        link, screenshot = await create_netflix_session(email, browser)
        if link:
            await wait_msg.edit_text(f"✅ تم إنشاء الجلسة! رابط الدخول:\n{link}")
        else:
            error_text = "❌ فشلت العملية. راجع السجلات لمعرفة السبب."
            if screenshot:
                await update.message.reply_photo(photo=screenshot, caption="لقطة من المتصفح عند حدوث الخطأ:")
                error_text += "\nتم إرسال لقطة الشاشة أعلاه، قد تفيد في التشخيص."
            await wait_msg.edit_text(error_text)
    except Exception as e:
        logger.exception("استثناء غير متوقع في handle_email")
        await wait_msg.edit_text("❌ حدث خطأ داخلي، حاول لاحقاً.")

# -------------------- بدء التشغيل --------------------
async def main():
    # ✅ تشغيل المتصفح الخفي عبر Camoufox
    async with Camoufox(headless=True, browser="chromium") as browser:
        logger.info("Camoufox يعمل بنجاح مع Chromium")

        # حفظ المتصفح لاستخدامه في ال handlers
        app = Application.builder().token(TOKEN).build()
        app.bot_data['browser'] = browser

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))

        webhook_url = os.environ.get('WEBHOOK_URL')
        if webhook_url:
            await app.run_webhook(
                listen="0.0.0.0",
                port=int(os.environ.get('PORT', 8443)),
                webhook_url=webhook_url
            )
        else:
            logger.info("تشغيل بالاستطلاع...")
            await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
