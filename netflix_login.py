import json
import asyncio
from playwright.async_api import async_playwright

async def login_netflix_with_cookies(cookies_json_str):
    try:
        cookies = json.loads(cookies_json_str)
        
        async with async_playwright() as p:
            # إعدادات متصفح قوية لتجنب اكتشاف البوت
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu'
                ]
            )
            
            # وكيل مستخدم (User-Agent) عشوائي وثابت
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # تنظيف وحقن الكوكيز
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
                # حماية من الأخطاء عند تمرير cookies
                if "hostOnly" in clean_cookie: del clean_cookie["hostOnly"]
                if "storeId" in clean_cookie: del clean_cookie["storeId"]
                
                await context.add_cookies([clean_cookie])
            
            # الذهاب إلى نيتفليكس وانتظار التوجيه
            await page.goto("https://www.netflix.com/browse")
            await page.wait_for_timeout(4000)
            
            # التحقق من وجود الملف الشخصي (تسجيل ناجح)
            if await page.locator("a[data-uia='profile-avatar']").count() > 0:
                session_url = page.url
                await browser.close()
                return {"status": "success", "message": "اكتمل التسجيل", "session_url": session_url}
            else:
                await browser.close()
                return {"status": "failed", "message": "الكوكيز غير صالحة أو انتهت صلاحيتها"}
                
    except Exception as e:
        return {"status": "error", "message": f"فشل الاتصال: {str(e)}"}
