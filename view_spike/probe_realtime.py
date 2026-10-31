# -*- coding: utf-8 -*-
r"""
PHASE 1 (tam) — do xem Studio cho doc VIEW THEO GIO cua 1 video bang cach nao.

  py -3.13 probe_realtime.py --mail VirgiliTraino95@gmail.com --video UeOxoZUN_UI

Luat: mo profile GPM qua API; ProfileUsingByOther -> DUNG, khong dong/kill.
Doc xong DONG profile ngay (chi profile ma script nay vua mo).
"""
import sys, os, json, time, argparse, datetime
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
from studio_collect import DEEP, wait_text          # noqa: E402
from scan_channels import all_profiles, match, start, stop   # noqa: E402

# Moi phan tu co aria-label / title (ke ca trong shadow DOM, ke ca SVG) — cot bieu do hay de so o day
ARIA = """() => {
  const out = [];
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
      if (el.shadowRoot) walk(el.shadowRoot);
      const a = el.getAttribute && (el.getAttribute('aria-label') || el.getAttribute('title'));
      if (a && /\\d/.test(a) && a.length < 300) out.push(el.tagName + ' :: ' + a);
      if (el.tagName === 'title' && /\\d/.test(el.textContent)) out.push('svg-title :: ' + el.textContent.trim());
  } };
  walk(document);
  return out;
}"""


def around(parts, key, n=40):
    for i, t in enumerate(parts):
        if key.lower() in t.lower():
            return parts[i:i + n]
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mail")
    ap.add_argument("--port", type=int, help="Chrome rieng (vd 9222 kenh haoviabattu) — chi attach, KHONG dong")
    ap.add_argument("--channel", help="channel id: vao /channel/<id> truoc de Studio dung dung kenh")
    ap.add_argument("--video", required=True)
    a = ap.parse_args()
    pid = None
    if a.port:
        ws = f"http://127.0.0.1:{a.port}"
    else:
        pid = match(all_profiles(), a.mail)
        if not pid:
            raise SystemExit(f"khong thay profile GPM cho {a.mail}")
        ws = start(pid)          # raise PROFILE_BUSY neu anh dang mo -> dung
    res = {"video": a.video, "at": datetime.datetime.now().isoformat(timespec="seconds")}
    try:
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(ws)
            page = br.contexts[0].new_page()
            page.bring_to_front()
            if a.channel:
                page.goto(f"https://studio.youtube.com/channel/{a.channel}", wait_until="domcontentloaded", timeout=90000)
                time.sleep(5)
                res["channel_url"] = page.url
            for attempt in range(2):     # bay #5: lan goto dau hay dung o root
                page.goto(f"https://studio.youtube.com/video/{a.video}/analytics/tab-overview/period-default",
                          wait_until="domcontentloaded", timeout=90000)
                parts = wait_text(page, ["Realtime", "Thời gian thực", "リアルタイム"], loops=15)
                if any(k in " ".join(parts) for k in ["Realtime", "Thời gian thực", "リアルタイム"]):
                    break
            res["a_deep_realtime"] = (around(parts, "Realtime") or around(parts, "Thời gian thực")
                                      or around(parts, "リアルタイム"))
            res["a_aria"] = page.evaluate(ARIA)
            page.screenshot(path=os.path.join(HERE, "state", f"probe_{a.video}.png"), full_page=True)
            page.close()
    finally:
        if pid:
            stop(pid)
    os.makedirs(os.path.join(HERE, "state"), exist_ok=True)
    out = os.path.join(HERE, "state", f"probe_{a.video}_{int(time.time())}.json")
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("DEEP quanh Realtime:", res["a_deep_realtime"])
    print("aria/title co so:", len(res["a_aria"]))
    for x in res["a_aria"][:80]:
        print("  ", x)
    print("->", out)


if __name__ == "__main__":
    main()
