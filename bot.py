import asyncio
import random
import string
import traceback
import requests
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "ضع_التوكن_هنا"

# الكوكيز السحري لعرض الـ 30 يومًا
MAGIC_COOKIE = {
    "name": "nfvdid",
    "value": "BQFmAAEBEE9JRlMuhcd1vZeyOZDGNsBgwt3MrI_af3LayzVVer6glzJvVpf97z33DXpKHBq9u0DnX0WJv5EuD1xSVUtIk9HEqcup0dtQ_aPOeD1ClWFBbYusKTD2yuO_aWV8_hyzEbgC_UGa_bLVoE2bGHdkptD2",
    "domain": ".netflix.com",
    "path": "/",
    "httpOnly": False,
    "secure": False,
    "sameSite": "Lax"
}

def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def get_temp_email():
    try:
        resp = requests.post(
            "https://api.mail.tm/accounts",
            json={"address": "", "password": "pass123"},
            timeout=10
        )
        data = resp.json()
        return data["address"]
    except Exception as e:
        logger.error(f"فشل البريد الوهمي: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 جاري تشغيل المتصفح...")

    async with async_playwright() as p:
        # إطلاق Chromium (موجود مسبقًا في الصورة)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # تطبيق التخفي
        await stealth_async(page)

        try:
            # ضبط الكوكيز على نطاق netflix
            await page.goto("https://www.netflix.com")
            await page.context.add_cookies([MAGIC_COOKIE])
            await page.goto("https://www.netflix.com/signup")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # التأكد اختياريًا من وجود نص 30 يوم
            content = await page.content()
            if "30 يوم" not in content and "30-day" not in content.lower():
                logger.warning("لم يتم رؤية عرض 30 يومًا، سنحاول المتابعة.")

            # إنشاء بريد وهمي
            email = get_temp_email()
            if not email:
                await update.message.reply_text("❌ فشل إنشاء بريد وهمي")
                return
            password = generate_password()

            # ملء النموذج
            await page.wait_for_selector('input[name="email"]', timeout=10000)
            await page.fill('input[name="email"]', email)
            await page.click('button:has-text("متابعة"), button:has-text("Continue")')
            await asyncio.sleep(2)

            if await page.is_visible('input[name="password"]'):
                await page.fill('input[name="password"]', password)
                await page.click('button:has-text("التالي"), button:has-text("Next")')
                await asyncio.sleep(3)

            # إبلاغ المستخدم
            await update.message.reply_text(
                f"✅ تم التسجيل بنجاح!\n\n"
                f"📧 البريد: `{email}`\n"
                f"🔒 كلمة المرور: `{password}`",
                parse_mode="Markdown"
            )

        except Exception as e:
            err = f"❌ فشلت العملية:\n{e}\n\n{traceback.format_exc()}"
            # تقسيم الرسالة الطويلة
            for chunk in [err[i:i+4000] for i in range(0, len(err), 4000)]:
                await update.message.reply_text(chunk)
        finally:
            await browser.close()

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    logger.info("البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
