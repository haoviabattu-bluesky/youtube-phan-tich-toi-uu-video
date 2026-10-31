# -*- coding: utf-8 -*-
r"""
PHASE 1 (tam) — ghi view CONG KHAI (Data API) moi N phut vao state/probe_api.csv
de doi chieu voi so Studio. 1 unit / lan (gom moi id vao 1 lan goi).

  py -3.13 probe_api_log.py --ids UeOxoZUN_UI,wUlSLQtGkTs --every 15 --hours 4
"""
import sys, os, csv, time, argparse, datetime
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
import spike_sources as s

ap = argparse.ArgumentParser()
ap.add_argument("--ids", required=True)
ap.add_argument("--every", type=float, default=15)
ap.add_argument("--hours", type=float, default=4)
a = ap.parse_args()
ids = a.ids.split(",")
out = os.path.join(HERE, "state", "probe_api.csv")
end = time.time() + a.hours * 3600
while time.time() < end:
    now = datetime.datetime.now().isoformat(timespec="seconds")
    try:
        st = s.videos_stats(ids)
        rows = [[now, vid, st.get(vid, {}).get("views"), s.UNITS_USED["n"]] for vid in ids]
    except Exception as e:
        rows = [[now, "ERR", str(e)[:120], s.UNITS_USED["n"]]]
    new = not os.path.exists(out)
    with open(out, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "video_id", "api_views", "units_used_cum"])
        w.writerows(rows)
    print(rows, flush=True)
    time.sleep(a.every * 60)
