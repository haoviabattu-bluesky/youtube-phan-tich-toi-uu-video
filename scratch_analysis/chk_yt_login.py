import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
ws = sys.argv[1]
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    ctx = br.contexts[0]
    print("pages", len(ctx.pages))
    for pg in ctx.pages:
        print(" -", pg.url)
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    pg.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(7000)
    print("URL:", pg.url)
    print("TITLE:", pg.title())
    print("LOGIN:", pg.evaluate("()=>!!document.querySelector('button#avatar-btn, ytd-topbar-menu-button-renderer #avatar-btn')"))
    print("avatar:", pg.evaluate("()=>document.querySelector('ytd-topbar-menu-button-renderer #avatar-btn')?.getAttribute('aria-label')"))
    print("consent:", pg.evaluate("()=>document.body.innerText.slice(0,300)"))
