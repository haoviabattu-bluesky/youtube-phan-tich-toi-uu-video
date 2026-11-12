import sys, json, time
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

ws = sys.argv[1]
q = sys.argv[2]
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    ctx = br.contexts[0]
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    pg.goto("https://www.youtube.com/results?search_query=" + __import__("urllib.parse", fromlist=["quote"]).quote(q),
            wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(6000)
    res = pg.evaluate("""() => {
      const out=[];
      for (const it of [...document.querySelectorAll('ytd-video-renderer')].slice(0,5)) {
        const a = it.querySelector('a#video-title');
        out.push({t:(a?.textContent||'').trim(), href:a?.href||'',
                  meta:(it.querySelector('#metadata-line')?.innerText||'').replace(/\\s+/g,' '),
                  ch:(it.querySelector('ytd-channel-name a')?.textContent||'').trim()});
      }
      return out;
    }""")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if res:
        pg.goto(res[0]["href"], wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(6000)
        diag = pg.evaluate("""() => {
          const likeSels=['ytd-watch-metadata #top-level-buttons-computed like-button-view-model button',
            'ytd-watch-metadata like-button-view-model button',
            'ytd-watch-metadata #segmented-like-button button',
            'segmented-like-dislike-button-view-model button'];
          const subSels=['ytd-watch-metadata #subscribe-button button','#owner #subscribe-button button',
            'ytd-subscribe-button-renderer button'];
          const pick=s=>{for(const x of s){const e=document.querySelector(x); if(e) return {sel:x,text:(e.innerText||'').trim().slice(0,40),aria:e.getAttribute('aria-pressed'),label:e.getAttribute('aria-label')}}return null};
          const v=document.querySelector('video.html5-main-video');
          return {title:document.querySelector('h1.ytd-watch-metadata yt-formatted-string')?.textContent.trim(),
                  dur:v?v.duration:0, paused:v?v.paused:null,
                  like:pick(likeSels), sub:pick(subSels),
                  likeAll:[...document.querySelectorAll('like-button-view-model button')].map(e=>({l:e.getAttribute('aria-label'),p:e.getAttribute('aria-pressed')})),
                  subAll:[...document.querySelectorAll('#subscribe-button button')].map(e=>e.innerText.trim().slice(0,30))};
        }""")
        print(json.dumps(diag, ensure_ascii=False, indent=1))
