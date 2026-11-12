import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
ws = sys.argv[1]
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    ctx = br.contexts[0]
    pg = ctx.pages[0]
    st = pg.evaluate("""() => {
      const movie = document.querySelector('#movie_player');
      const skip = document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern');
      return {
        adShowing: !!document.querySelector('.ad-showing'),
        classes: movie? movie.className : null,
        adBadge: document.querySelector('.ytp-ad-badge, .ytp-ad-simple-ad-badge')?.innerText,
        adDuration: document.querySelector('.ytp-ad-duration-remaining')?.innerText,
        skipBtn: skip? {txt: skip.innerText, vis: skip.offsetParent!==null} : null,
        skipAll: [...document.querySelectorAll('[class*=skip-ad], [class*=ad-skip]')].map(e=>({c:e.className, t:e.innerText})),
        text: (document.querySelector('.ytp-ad-player-overlay-layout')?.innerText||'').slice(0,200)
      };
    }""")
    print(json.dumps(st, ensure_ascii=False, indent=1))
