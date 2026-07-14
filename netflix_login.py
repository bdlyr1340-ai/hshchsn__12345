
import json
import asyncio
from camoufox import AsyncCamoufox

async def login_netflix_with_cookies(cookies_json_str):
    """
    يستلم الكوكيز بصيغة نص JSON، يقوم بحقنها في المتصفح (Camoufox)
    ويسجل الدخول، ثم يعيد رابط الجلسة أو رسالة النجاح.
    """
    try:
        cookies = json.loads(cookies_json_str)
        
        # تهيئة المتصفح مع حماية Camoufox (مكافحة الكشف)
        async with AsyncCamoufox(headless=True) as browser:
            page = await browser.new_page()
            
            # تحويل الكوكيز إلى صيغة Playwright
            for cookie in cookies:
                # تنظيف الحقول غير المدعومة
                clean_cookie = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": cookie.get("path", "/"),
                    "secure": cookie.get("secure", False),
                    "httpOnly": cookie.get("httpOnly", False),
                    "sameSite": cookie.get("sameSite", "Lax"),
                    "expires": int(cookie.get("expirationDate", 0))  # تحويل التاريخ
                }
                await page.context.add_cookies([clean_cookie])
            
            # الذهاب إلى نيتفليكس
            await page.goto("https://www.netflix.com/browse")
            await page.wait_for_timeout(3000)  # انتظار التوجيه التلقائي
            
            # التحقق من نجاح تسجيل الدخول (وجود زر الخروج أو ملف التعريف)
            if await page.locator("a[data-uia='profile-avatar']").count() > 0 or \
               await page.locator("button:has-text('Sign Out')").count() > 0:
                
                # محاولة استخراج رابط الجلسة (رابط الملف الشخصي)
                session_url = page.url
                return {"status": "success", "message": "اكتمل التسجيل", "session_url": session_url}
            else:
                return {"status": "failed", "message": "الكوكيز غير صالحة أو انتهت صلاحيتها"}
                
    except Exception as e:
        return {"status": "error", "message": f"حدث خطأ: {str(e)}"}
