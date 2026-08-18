#!/usr/bin/env python3
import json
import os
import sys
from playwright.sync_api import sync_playwright

SITES = [
    {
        "name": "NodeSeek",
        "url": "https://www.nodeseek.com",
        "cookie_env": "NODESEEK_COOKIES",
    },
    {
        "name": "NodeLoc",
        "url": "https://www.nodeloc.com/latest",
        "cookie_env": "NODELOC_COOKIES",
    },
    {
        "name": "Linux.SB",
        "url": "https://linux.sb",
        "cookie_env": "LINUX_SB_COOKIES",
    },
]

CHECKIN_TEXTS = ["签到", "每日签到", "打卡", "领取", "Check in", "Check-in"]
SUCCESS_TEXTS = ["签到成功", "已签到", "今日已签到", "打卡成功", "领取成功"]


def load_cookies(env_name, site_url):
    raw = os.environ.get(env_name, "").strip()
    if not raw:
        raise RuntimeError(f"缺少 GitHub Secret: {env_name}")

    try:
        cookies = json.loads(raw)
        if isinstance(cookies, list):
            return cookies
    except json.JSONDecodeError:
        pass

    cookies = []
    for item in raw.split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue
        name, value = item.split("=", 1)
        cookies.append({
            "name": name.strip(),
            "value": value.strip(),
            "url": site_url,
        })

    if not cookies:
        raise ValueError(f"{env_name} 必须是完整 Cookie 字符串，例如 name=value; name2=value2")
    return cookies


def checkin(browser, site):
    context = browser.new_context(
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/127.0.0.0 Safari/537.36"
        ),
    )

    try:
        context.add_cookies(load_cookies(site["cookie_env"], site["url"]))
        page = context.new_page()
        page.goto(site["url"], wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)

        body_text = page.locator("body").inner_text(timeout=10000)
        if any(text in body_text for text in SUCCESS_TEXTS):
            print(f"[成功] {site['name']}: 今日已经签到")
            return True

        for text in CHECKIN_TEXTS:
            locator = page.get_by_text(text, exact=True)
            if locator.count() == 0:
                locator = page.get_by_text(text, exact=False)

            for index in range(locator.count()):
                target = locator.nth(index)
                if not target.is_visible():
                    continue

                target.click(timeout=10000)
                page.wait_for_timeout(3000)
                result_text = page.locator("body").inner_text(timeout=10000)

                if any(success in result_text for success in SUCCESS_TEXTS):
                    print(f"[成功] {site['name']}: 签到成功")
                else:
                    print(f"[完成] {site['name']}: 已点击“{text}”，请结合 Actions 日志确认结果")
                return True

        page.screenshot(path=f"{site['name'].lower().replace('.', '_')}-debug.png", full_page=True)
        print(f"[失败] {site['name']}: 未找到签到入口，已保存调试截图", file=sys.stderr)
        return False
    except Exception as exc:
        print(f"[失败] {site['name']}: {exc}", file=sys.stderr)
        return False
    finally:
        context.close()


def main():
    failed = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for site in SITES:
                if not checkin(browser, site):
                    failed.append(site["name"])
        finally:
            browser.close()

    if failed:
        print("签到失败的网站: " + ", ".join(failed), file=sys.stderr)
        return 1

    print("所有网站签到任务执行完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
