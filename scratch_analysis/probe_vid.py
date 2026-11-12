import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
ws = sys.argv[1]
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    ctx = br.contexts[0]
    pg = ctx.pages[0]
    st = pg.evaluate("""() => {
      const pr = window.ytInitialPlayerResponse;
      const v = document.querySelector('video.html5-main-video');
      return {
        url: location.href,
        docTitle: document.title,
        videoId: pr?.videoDetails?.videoId,
        lengthSec: pr?.videoDetails?.lengthSeconds,
        author: pr?.videoDetails?.author,
        prTitle: pr?.videoDetails?.title,
        elT: v? v.currentTime:0, elD: v? v.duration:0, paused: v? v.paused:null,
        adShowing: !!document.querySelector('.ad-showing'),
      };
    }""")
    print(json.dumps(st, ensure_ascii=False, indent=1))
