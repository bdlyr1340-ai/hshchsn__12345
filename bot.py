import os
import asyncio
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from playwright.async_api import async_playwright

# --- الإعدادات ---
# ضع توكن البوت هنا أو في متغيرات البيئة في Railway
API_TOKEN = os.getenv("BOT_TOKEN") 

# الكوكيز التي زودتني بها
COOKIES_DATA = [
    {"name": "netflix-sans-normal-3-loaded", "value": "true", "domain": ".netflix.com", "path": "/"},
    {"name": "SecureNetflixId", "value": "v%3D3%26mac%3DAQEAEQABABQ6aF0HZ8DsqIo_PhF7ZqIn4Pnkr9eRfa8.%26dt%3D1783653781333", "domain": ".netflix.com", "path": "/"},
    {"name": "gsid", "value": "e1335f92-02b6-43d9-a5dd-c979841186f3", "domain": ".netflix.com", "path": "/"},
    {"name": "NetflixId", "value": "v%3D3%26ct%3DBgjHlOvcAxK7AQ6aWc332xABBe3_4TFi_GhYz6bu_SppiID9W173968rwXGgBZ5FOguy1o_nypEEzJFpJgmH0c87meJqBoXmkDG-3fRhPBkFJTw4N7FdSlN0L-D1Ihh-QS3KpejkBqY-jawZSvsTk7_j4UywDGYUdSSEksmaOJUWffx0dkqHTtce0mtk26U5ed1HqmdrMIXbF4_wTrJay86xSzumhWvu6NCztzpwtR73CSf9ei3-8Zhv4lR_akcGOLIpWaUYBiIOCgzRZAUwFliOAy-sUmU.", "domain": ".netflix.com", "path": "/"},
    {"name": "flwssn", "value": "0c34d834-9769-4f10-8fbe-8ec245d9746f", "domain": ".netflix.com", "path": "/"},
    {"name": "netflix-sans-bold-3-loaded", "value": "true", "domain": ".netflix.com", "path": "/"},
    {"name": "nfvdid", "value": "BQFmAAEBEE9JRlMuhcd1vZeyOZDGNsBgwt3MrI_af3LayzVVer6glzJvVpf97z33DXpKHBq9u0DnX0WJv5EuD1xSVUtIk9HEqcup0dtQ_aPOeD1ClWFBbYusKTD2yuO_aWV8_hyzEbgC_UGa_bLVoE2bGHdkptD2", "domain": ".netflix.com", "path": "/"}
]

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    waiting_for_email = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("👋 أهلاً بك في بوت Netflix.\nلقد تم تجهيز الكوكيز بنجاح ✅\n\nالآن، يرجى إرسال الإيميل المراد ربطه بالجلسة:")
    await state.set_state(Form.waiting_for_email)

@dp.message(Form.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text
    await message.answer(f"⏳ جاري محاولة تسجيل الدخول للإيميل: {email}...\nيرجى الانتظار ثواني.")
    
    try:
        success = await check_netflix_session(email)
        if success:
            await message.answer(f"✅ اكتمل التسجيل بنجاح!\n\n📧 الإيميل: {email}\n🔗 حالة الجلسة: تعمل بنجاح\n\nيمكنك الآن استخدام الحساب.")
        else:
            await message.answer("❌ فشل تسجيل الدخول. الكوكيز قد تكون منتهية الصلاحية أو الإيميل غير مطابق.")
    except Exception as e:
        await message.answer(f"⚠️ حدث خطأ تقني: {str(e)}")
    
    await state.clear()

async def check_netflix_session(email):
    async with async_playwright() as p:
        # تشغيل المتصفح مع إعدادات تمنع اكتشاف الروبوتات
        browser = await p.chromium.launch(headless=True)
        
        # إنشاء سياق متصفح جديد وبصمة رقمية تشبه البشر
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 1. حقن الكوكيز أولاً لتفعيل "عرض المجاني"
        await context.add_cookies(COOKIES_DATA)
        
        page = await context.new_page()
        
        try:
            # 2. التوجه إلى صفحة تسجيل الدخول أو الصفحة الرئيسية لربط الإيميل بالجلسة
            # سنحاول الدخول مباشرة لصفحة الحساب لتربيط الإيميل
            await page.goto(f"https://www.netflix.com/login", wait_until="networkidle")
            
            # محاولة إدخال الإيميل في حقل التسجيل لربطه بالكوكيز الموجودة
            # ملاحظة: إذا كانت الكوكيز تسجل الدخول تلقائياً، سيتجاوز هذه الخطوة
            if await page.query_selector('input[name="userLoginId"]'):
                await page.fill('input[name="userLoginId"]', email)
                await page.click('button[type="submit"]')
                await page.wait_for_timeout(5000) # انتظار التفعيل

            # 3. التحقق هل تم تفعيل العرض والدخول للحساب؟
            # نبحث عن كلمات تدل على نجاح الدخول أو وجود الحساب
            current_url = page.url
            if "browse" in current_url or "YourAccount" in current_url or "netflix.com" in current_url:
                # التأكد من أننا لسنا في صفحة "خطأ" أو "تسجيل دخول"
                if "login" not in current_url:
                    await browser.close()
                    return True
            
            await browser.close()
            return False
        except Exception as e:
            print(f"Error during process: {e}")
            await browser.close()
            return False

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
