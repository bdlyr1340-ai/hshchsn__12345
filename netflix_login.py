import json
import asyncio
from playwright.async_api import async_playwright

async def login_netflix_with_cookies(cookies_json_str):
    try:
        cookies = json.loads(cookies_json_str)
        
        async with async_playwright() as p:
            # تشغيل المتصفح مع إعدادات مكافحة الكشف (Anti-bot detection)
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox'
                ]
            )
            
            # إضافة User-Agent عشوائي لزيادة المصداقية
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # تحويل الكوكيز وتنظيفها
            for cookie in cookies:
                clean_cookie = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": cookie.get("path", "/"),
                    "secure": cookie.get("secure", False),
                    "httpOnly": cookie.get("httpOnly", False),
                    "sameSite": cookie.get("sameSite", "Lax"),
                    "expires": int(cookie.get("expirationDate", 0))
                }
                await context.add_cookies([clean_cookie])
            
            # الذهاب إلى نيتفليكس
            await page.goto("https://www.netflix.com/browse")
            await page.wait_for_timeout(4000)  # انتظار توجيه الصفحة
            
            # التحقق من النجاح
            if await page.locator("a[data-uia='profile-avatar']").count() > 0:
                session_url = page.url
                await browser.close()
                return {"status": "success", "message": "اكتمل التسجيل", "session_url": session_url}
            else:
                await browser.close()
                return {"status": "failed", "message": "الكوكيز غير صالحة أو انتهت صلاحيتها"}
                
    except Exception as e:
        return {"status": "error", "message": f"حدث خطأ: {str(e)}"}
