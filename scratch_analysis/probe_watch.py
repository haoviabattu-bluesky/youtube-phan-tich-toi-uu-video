import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
ws = sys.argv[1]
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    ctx = br.contexts[0]
    for pg in ctx.pages:
        if "youtube.com/watch" in pg.url:
            st = pg.evaluate("""() => {
              const v=document.querySelector('video.html5-main-video');
              const like=[...document.querySelectorAll('like-button-view-model button')].map(e=>e.getAttribute('aria-pressed'));
              const sub=[...document.querySelectorAll('#subscribe-button button')].map(e=>e.innerText.trim());
              return {url:location.href, t:v?v.currentTime:0, d:v?v.duration:0, paused:v?v.paused:null,
                      title:document.querySelector('h1.ytd-watch-metadata yt-formatted-string')?.textContent.trim(),
                      like:like, sub:sub};
            }""")
            print(json.dumps(st, ensure_ascii=False, indent=1))
