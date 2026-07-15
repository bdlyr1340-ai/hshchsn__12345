import asyncio
import random
import string
import requests
from camoufox import Camoufox
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "ضع_توكن_البوت_هنا"
TEMP_MAIL_API = "https://api.mail.tm"

# الكوكيز المقدّم (يحوّل العرض إلى 30 يومًا)
MAGIC_COOKIE = {
    "name": "nfvdid",
    "value": "BQFmAAEBEE9JRlMuhcd1vZeyOZDGNsBgwt3MrI_af3LayzVVer6glzJvVpf97z33DXpKHBq9u0DnX0WJv5EuD1xSVUtIk9HEqcup0dtQ_aPOeD1ClWFBbYusKTD2yuO_aWV8_hyzEbgC_UGa_bLVoE2bGHdkptD2",
    "domain": ".netflix.com",
    "path": "/",
    "secure": False,
    "httpOnly": False,
    "sameSite": "Lax",
    "expires": 1818612716  # تاريخ انتهاء الكوكيز (اختياري لكن مفيد)
}

def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def get_temp_email():
    try:
        resp = requests.post("https://api.mail.tm/accounts",
                             json={"address": "", "password": "pass123"})
        data = resp.json()
        return data["address"]
    except Exception as e:
        print("خطأ البريد:", e)
        return None

async def fill_form(page, email, password):
    """تعبئة النموذج بعد ظهور خطة 30 يوم"""
    try:
        # انتظار حقل الإيميل
        await page.wait_for_selector('input[name="email"]', timeout=10000)
        await page.fill('input[name="email"]', email)
        # الضغط على زر المتابعة
        await page.click('button:has-text("متابعة"), button:has-text("Continue")')
        await asyncio.sleep(2)

        # إذا طلب كلمة مرور (حساب جديد)
        if await page.is_visible('input[name="password"]'):
            await page.fill('input[name="password"]', password)
            await page.click('button:has-text("التالي"), button:has-text("Next")')
            await asyncio.sleep(3)
        return True
    except Exception as e:
        print("خطأ في تعبئة النموذج:", e)
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 جاري بدء العملية...")

    async with Camoufox(headless=True, os=["windows"]) as browser:
        page = await browser.new_page()
        try:
            # الخطوة 1: تعيين الكوكيز على نطاق netflix.com
            # يجب أن نكون على النطاق أولاً لوضع الكوكيز
            await page.goto("https://www.netflix.com")
            await page.context.add_cookies([MAGIC_COOKIE])
            await asyncio.sleep(1)

            # الخطوة 2: الذهاب لصفحة الاشتراك (ستظهر خطة 30 يوم)
            await page.goto("https://www.netflix.com/signup")
            await asyncio.sleep(2)

            # التحقق السريع من وجود 30 يومًا (اختياري)
            content = await page.content()
            if "30 يوم" not in content and "30-day" not in content.lower():
                # يمكن أن نضيف محاولة أخرى أو نرسل تحذير
                pass  # نكمل رغم ذلك

            # الخطوة 3: إنشاء بريد وهمي
            email = get_temp_email()
            if not email:
                await update.message.reply_text("❌ فشل إنشاء بريد وهمي")
                return
            password = generate_password()

            # الخطوة 4: تعبئة النموذج
            if await fill_form(page, email, password):
                await update.message.reply_text(
                    f"✅ تم التسجيل بنجاح!\n\n"
                    f"📧 البريد: `{email}`\n"
                    f"🔒 كلمة المرور: `{password}`\n\n"
                    f"الرجاء استخدامه فوراً.",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ فشل في إكمال التسجيل")

        except Exception as e:
            await update.message.reply_text(f"❌ خطأ: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
