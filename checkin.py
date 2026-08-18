#!/usr/bin/env python3
import asyncio
import json
import os
import re
import sys
from urllib.parse import urlparse
from playwright.async_api import async_playwright

HEADLESS = os.getenv("HEADLESS", "true").lower() != "false"
TIMEOUT = int(os.getenv("TIMEOUT_MS", "30000"))

SITES = [
    {
        "name": "NodeLoc",
        "url": "https://www.nodeloc.com/latest",
        "cookie_env": "NODELOC_COOKIE",
        "success": ["今日已签到", "今天已签到", "已签到", "签到成功", "获得能量", "领取成功"],
        "buttons": ["每日签到", "立即签到", "签到"],
    },
    {
        "name": "Linux.SB",
        "url": "https://linux.sb/daily_checkin",
        "cookie_env": "LINUXSB_COOKIE",
        "success": ["今日已签到", "今天已签到", "已签到", "签到成功", "连续签到", "领取成功"],
        "buttons": ["立即签到", "每日签到", "签到"],
    },
]


def parse_cookie_header(raw, domain):
    cookies = []
    for part in raw.split(";"):
        if "=" not in part:
            continue
        name, value = part.strip().split("=", 1)
        if name:
            cookies.append({
                "name": name,
                "value": value,
                "domain": domain,
                "path": "/",
                "secure": True,
            })
    return cookies


async def text(page):
    try:
        return await page.locator("body").inner_text(timeout=8000)
    except Exception:
        return ""


async def click_label(page, labels):
    for label in labels:
        rx = re.compile(re.escape(label), re.I)
        locators = [
            page.get_by_role("button", name=rx),
            page.get_by_role("link", name=rx),
            page.get_by_text(rx, exact=False),
        ]
        for locator in locators:
            try:
                if await locator.count() and await locator.first.is_visible():
                    await locator.first.click(timeout=8000)
                    return label
            except Exception:
                continue
    return None


async def screenshot(page, name):
    try:
        await page.screenshot(path=f"{name}.png", full_page=True)
    except Exception:
        pass


async def run_nodeseek(browser):
    raw = os.getenv("NODESEEK_COOKIE", "").strip()
    if not raw:
        return {"site": "NodeSeek", "ok": False, "message": "缺少 Secret: NODESEEK_COOKIE"}

    context = await browser.new_context(locale="zh-CN", timezone_id="Asia/Shanghai")
    await context.add_cookies(parse_cookie_header(raw, "www.nodeseek.com"))
    page = await context.new_page()
    page.set_default_timeout(TIMEOUT)

    try:
        # Cookie 已在首次访问前注入。先访问首页建立会话，再进入登录后才显示内容的签到页。
        await page.goto("https://www.nodeseek.com/", wait_until="domcontentloaded", timeout=TIMEOUT)
        await page.wait_for_timeout(3000)

        home = await text(page)
        title = await page.title()
        if "Just a moment" in title or "Cloudflare" in home or "Verify you are human" in home:
            return {"site": "NodeSeek", "ok": False, "message": "遇到 Cloudflare 验证，GitHub Runner 无法恢复登录", "url": page.url}

        await page.goto("https://www.nodeseek.com/board", wait_until="domcontentloaded", timeout=TIMEOUT)
        await page.wait_for_timeout(5000)
        board = await text(page)

        if "Just a moment" in await page.title() or "Verify you are human" in board:
            return {"site": "NodeSeek", "ok": False, "message": "签到页遇到 Cloudflare 验证", "url": page.url}

        already = ["今日已签到", "今天已完成签到", "请勿重复操作", "当前排名"]
        if any(word in board for word in already):
            return {"site": "NodeSeek", "ok": True, "message": "今天已经签到", "url": page.url}

        # /board 登录后通常直接出现奖励按钮。若只显示导航签到图标，先点击图标。
        clicked = await click_label(page, ["鸡腿 x 5", "鸡腿×5", "固定 5", "固定5", "试试手气"])
        if not clicked:
            for selector in ['[title="签到"]', 'span[title="签到"]', 'a[title="签到"]']:
                icon = page.locator(selector)
                try:
                    if await icon.count() and await icon.first.is_visible():
                        await icon.first.click(timeout=8000)
                        await page.wait_for_timeout(2000)
                        break
                except Exception:
                    pass
            clicked = await click_label(page, ["鸡腿 x 5", "鸡腿×5", "固定 5", "固定5", "试试手气"])

        if not clicked:
            login_hint = any(word in board for word in ["登录", "注册"]) and "退出登录" not in board
            message = "NODESEEK_COOKIE 未恢复登录状态，/board 未显示签到内容" if login_hint else "已打开 /board，但未找到奖励按钮，可能是 Cookie、风控或页面改版"
            return {"site": "NodeSeek", "ok": False, "message": message, "url": page.url}

        await page.wait_for_timeout(3500)
        result_text = await text(page)
        success_words = ["签到成功", "获得", "鸡腿", "已完成签到", "请勿重复操作", "当前排名"]
        ok = any(word in result_text for word in success_words)
        return {
            "site": "NodeSeek",
            "ok": ok,
            "message": f"已点击 {clicked}" + ("，检测到签到结果" if ok else "，但未检测到明确结果"),
            "url": page.url,
        }
    except Exception as exc:
        return {"site": "NodeSeek", "ok": False, "message": f"{type(exc).__name__}: {exc}", "url": page.url}
    finally:
        await screenshot(page, "nodeseek")
        await context.close()


async def run_generic(browser, site):
    raw = os.getenv(site["cookie_env"], "").strip()
    if not raw:
        return {"site": site["name"], "ok": False, "message": f"缺少 Secret: {site['cookie_env']}"}

    domain = urlparse(site["url"]).hostname
    context = await browser.new_context(locale="zh-CN", timezone_id="Asia/Shanghai")
    await context.add_cookies(parse_cookie_header(raw, domain))
    page = await context.new_page()
    page.set_default_timeout(TIMEOUT)
    slug = site["name"].lower().replace(".", "")

    try:
        requested_url = site["url"]
        await page.goto(requested_url, wait_until="domcontentloaded", timeout=TIMEOUT)
        await page.wait_for_timeout(3500)

        if "/login" in page.url.lower():
            return {
                "site": site["name"],
                "ok": False,
                "message": f"已请求 {requested_url}，但 Cookie 无效，网站重定向到登录页",
                "requested_url": requested_url,
                "url": page.url,
            }

        before = await text(page)
        if any(word in before for word in site["success"]):
            return {"site": site["name"], "ok": True, "message": "今天已经签到", "requested_url": requested_url, "url": page.url}

        clicked = await click_label(page, site["buttons"])
        if not clicked:
            return {"site": site["name"], "ok": False, "message": "未找到签到按钮，可能是 Cookie 无效或页面改版", "requested_url": requested_url, "url": page.url}

        await page.wait_for_timeout(3500)
        if "/login" in page.url.lower():
            return {"site": site["name"], "ok": False, "message": "点击后跳转到登录页，Cookie 无效", "requested_url": requested_url, "url": page.url}

        after = await text(page)
        ok = any(word in after for word in site["success"])
        return {
            "site": site["name"],
            "ok": ok,
            "message": f"已点击 {clicked}" + ("，检测到签到成功" if ok else "，但未检测到明确成功提示"),
            "requested_url": requested_url,
            "url": page.url,
        }
    except Exception as exc:
        return {"site": site["name"], "ok": False, "message": f"{type(exc).__name__}: {exc}", "url": page.url}
    finally:
        await screenshot(page, slug)
        await context.close()


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        results = [await run_nodeseek(browser)]
        for site in SITES:
            results.append(await run_generic(browser, site))
        await browser.close()

    for result in results:
        print(json.dumps(result, ensure_ascii=False))
    print("\n汇总：" + json.dumps(results, ensure_ascii=False, indent=2))
    if any(not result["ok"] for result in results):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
