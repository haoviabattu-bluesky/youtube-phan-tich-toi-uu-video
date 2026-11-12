# -*- coding: utf-8 -*-
"""Doc tab Lane-P / Lane-GEO: A:S + mau vang cot K. Khong ghi gi."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from daily_sheet import svc, read_tab

tabs = sys.argv[1:] or ["Lane-P", "Lane-GEO"]
s = svc()
out = {}
for tab in tabs:
    rows, yel = read_tab(s, tab)
    print("=" * 100)
    print(f"TAB {tab}: {len(rows)} dong")
    for i, r in enumerate(rows, start=1):
        r = list(r) + [""] * (19 - len(r))
        A, E, G, J, K, L = r[0], r[4], r[6], r[9], r[10], r[11]
        N, O, P, Q, R, S = r[13], r[14], r[15], r[16], r[17], r[18]
        title = (r[1] or "")[:40]
        print(f"[{i}] K_yellow={yel.get(i)} A={A!r} L={L!r} N={N!r} O={O!r} P={P!r} Q={Q!r} R={R!r} S={S!r} | B={title!r}")
        print(f"      K={K!r}")
    out[tab] = [[str(c) for c in r] + [bool(yel.get(i))] for i, r in enumerate(rows, start=1)]
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sheet_P_GEO_now.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
