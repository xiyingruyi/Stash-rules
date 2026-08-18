#!/usr/bin/env python3
import asyncio, json, os, re, sys
from urllib.parse import urlparse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

HEADLESS = os.getenv("HEADLESS", "true").lower() != "false"
TIMEOUT = int(os.getenv("TIMEOUT_MS", "30000"))

SITES = [
    {
        "name": "NodeSeek",
        "url": "https://www.nodeseek.com/board",
        "cookie_env": "NODESEEK_COOKIE",
        "success": ["今日已签到", "签到成功", "获得鸡腿", "当前排名"],
        "buttons": ["鸡腿 x 5", "鸡腿×5", "固定 5", "固定5", "试试手气", "签到"],
    },
    {
        "name": "NodeLoc",
        "url": "https://www.nodeloc.com/latest",
        "cookie_env": "NODELOC_COOKIE",
        "success": ["今日已签到", "已签到", "签到成功", "获得能量"],
        "buttons": ["每日签到", "签到"],
        "discovery_urls": ["https://www.nodeloc.com/checkin", "https://www.nodeloc.com/daily_checkin"],
    },
    {
        "name": "Linux.SB",
        "url": "https://www.linux.sb/daily_checkin",
        "cookie_env": "LINUXSB_COOKIE",
        "success": ["今日已签到", "已签到", "签到成功", "获得"],
        "buttons": ["每日签到", "立即签到", "签到"],
    },
]

def parse_cookie_header(raw: str, domain: str):
    cookies=[]
    for part in raw.split(';'):
        if '=' not in part: continue
        name, value = part.strip().split('=', 1)
        if name:
            cookies.append({"name": name, "value": value, "domain": domain, "path": "/", "secure": True})
    return cookies

async def body_text(page):
    try: return await page.locator('body').inner_text(timeout=5000)
    except Exception: return ''

async def click_first(page, labels):
    for label in labels:
        patterns = [
            page.get_by_role("button", name=re.compile(re.escape(label), re.I)),
            page.get_by_role("link", name=re.compile(re.escape(label), re.I)),
            page.get_by_text(re.compile(re.escape(label), re.I), exact=False),
        ]
        for loc in patterns:
            try:
                if await loc.count() and await loc.first.is_visible():
                    await loc.first.click(timeout=8000)
                    return label
            except Exception:
                pass
    return None

async def run_site(browser, site):
    raw=os.getenv(site['cookie_env'], '').strip()
    if not raw:
        return {"site":site['name'], "ok":False, "message":f"缺少 Secret: {site['cookie_env']}"}
    context=await browser.new_context(locale='zh-CN', timezone_id='Asia/Shanghai')
    domain=urlparse(site['url']).hostname
    await context.add_cookies(parse_cookie_header(raw, domain))
    page=await context.new_page(); page.set_default_timeout(TIMEOUT)
    urls=[site['url']] + site.get('discovery_urls', [])
    try:
        for url in urls:
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=TIMEOUT)
                await page.wait_for_timeout(2500)
            except Exception:
                continue
            if '/login' in page.url.lower():
                return {"site":site['name'], "ok":False, "message":"Cookie 无效，已跳转到登录页", "url":page.url}
            before=await body_text(page)
            if any(x in before for x in site['success']):
                return {"site":site['name'], "ok":True, "message":"今天已经签到", "url":page.url}
            if site['name'] == 'NodeSeek':
                icon=page.locator('[title="签到"]')
                if await icon.count() and await icon.first.is_visible():
                    await icon.first.click(timeout=8000)
                    await page.wait_for_timeout(1500)
                clicked=await click_first(page, ["鸡腿 x 5", "鸡腿×5", "固定 5", "固定5", "试试手气"])
            else:
                clicked=await click_first(page, site['buttons'])
            if clicked:
                await page.wait_for_timeout(3000)
                if '/login' in page.url.lower():
                    return {"site":site['name'], "ok":False, "message":"签到时跳转到登录页，Cookie 无效", "url":page.url}
                after=await body_text(page)
                ok=any(x in after for x in site['success'])
                msg=f"签到成功，已点击：{clicked}" if ok else f"已点击 {clicked}，但未检测到明确成功提示"
                return {"site":site['name'], "ok":ok, "message":msg, "url":page.url}
        return {"site":site['name'], "ok":False, "message":"未找到签到入口，可能是 Cookie 失效、风控或页面改版", "url":page.url}
    except Exception as e:
        return {"site":site['name'], "ok":False, "message":f"{type(e).__name__}: {e}", "url":page.url}
    finally:
        try:
            await page.screenshot(path=f"{site['name'].lower().replace('.', '')}.png", full_page=True)
        except Exception: pass
        await context.close()

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=HEADLESS)
        results=[]
        for site in SITES:
            result=await run_site(browser, site)
            results.append(result)
            print(json.dumps(result, ensure_ascii=False))
        await browser.close()
    failed=[r for r in results if not r['ok']]
    print("\n汇总：" + json.dumps(results, ensure_ascii=False, indent=2))
    if failed: sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
