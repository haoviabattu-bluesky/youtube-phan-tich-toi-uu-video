import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
ws = sys.argv[1]
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    ctx = br.contexts[0]
    print("pages:", len(ctx.pages))
    for i, pg in enumerate(ctx.pages):
        try:
            st = pg.evaluate("""() => {
              const v=document.querySelector('video.html5-main-video');
              return {url:location.href, t:v?v.currentTime:0, d:v?v.duration:0, paused:v?v.paused:null,
                      title:document.querySelector('h1.ytd-watch-metadata yt-formatted-string')?.textContent.trim()};
            }""")
        except Exception as e:
            st = {"err": str(e)}
        print(i, json.dumps(st, ensure_ascii=False))
