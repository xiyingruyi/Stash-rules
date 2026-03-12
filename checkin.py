import os
import re
import time
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

CHECKIN_URL = "https://gpt.qt.cool/checkin"
API_KEY = os.environ.get("API_KEY")

def solve_math(text):
    """自动算数学题"""
    text = text.replace('×', '*').replace('÷', '/')
    match = re.search(r'(\d+)\s*([\+\-\*\/])\s*(\d+)', text)
    if match:
        a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
        if op == '+': return a + b
        if op == '-': return a - b
        if op == '*': return a * b
        if op == '/': return a // b if b != 0 else 0
    return None

def main():
    if not API_KEY:
        print("错误：没有设置 API_KEY")
        sys.exit(1)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("打开网页...")
            page.goto(CHECKIN_URL, wait_until="networkidle")
            time.sleep(2)
            
            # 检查是否已签到
            body = page.inner_text("body")
            if "今日已签到" in body or "已签到" in body:
                print("今天已经签到过了，不用签")
                return
            
            # 填密钥
            print("输入密钥...")
            page.fill('input[type="text"]', API_KEY)
            
            # 找算术题并计算
            captcha = ""
            for selector in ['.captcha', '#captcha', 'img', '.verify']:
                try:
                    if page.locator(selector).is_visible():
                        captcha = page.inner_text(selector) or page.get_attribute(selector, 'alt') or ""
                        break
                except:
                    pass
            
            if not captcha:
                captcha = page.inner_text("body")
            
            answer = solve_math(captcha)
            if answer:
                print(f"算出来答案是：{answer}")
                # 填答案
                try:
                    page.fill('input[type="number"]', str(answer))
                except:
                    inputs = page.locator('input').all()
                    if len(inputs) >= 2:
                        inputs[1].fill(str(answer))
            
            # 点击签到
            print("点击签到...")
            for btn_text in ['签到', '提交', 'Check', '确认']:
                try:
                    page.click(f'button:has-text("{btn_text}")', timeout=2000)
                    break
                except:
                    continue
            
            time.sleep(3)
            print("签到完成")
            
        except Exception as e:
            print(f"出错了：{e}")
            page.screenshot(path="screenshot.png")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
