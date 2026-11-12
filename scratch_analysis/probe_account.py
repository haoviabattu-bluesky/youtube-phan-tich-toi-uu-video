# -*- coding: utf-8 -*-
"""Doc email tai khoan + channel id that cua profile dang login."""
import sys, time, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

WS = sys.argv[1]

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.youtube.com/account", wait_until="domcontentloaded", timeout=90000)
    time.sleep(6)
    info = page.evaluate("""() => {
      const txt = document.body.innerText || '';
      const emails = (txt.match(/[\\w.+-]+@[\\w.-]+\\.[a-z]{2,}/gi)||[]).slice(0,5);
      const name = (document.querySelector('#name, ytd-account-profile-section #name')?.textContent||'').trim();
      const ch = document.querySelector('ytd-channel-profile-section a#channel-link, a#channel-link');
      return {name: name, emails: emails, channel_href: ch ? ch.getAttribute('href') : null,
              body_head: txt.slice(0, 700)};
    }""")
    print(json.dumps(info, ensure_ascii=False, indent=1))
    # channel id qua trang channel
    page.goto("https://www.youtube.com/channel_switcher", wait_until="domcontentloaded", timeout=90000)
    time.sleep(5)
    ch = page.evaluate("""() => Array.from(document.querySelectorAll('a')).filter(a=>(a.href||'').includes('/channel/')||(a.href||'').includes('/@')).slice(0,10).map(a=>({href:a.getAttribute('href'), text:(a.textContent||'').trim().slice(0,60)}))""")
    print("CHANNEL_SWITCHER:", json.dumps(ch, ensure_ascii=False, indent=1))
    br.close()
