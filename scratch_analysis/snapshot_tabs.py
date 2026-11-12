# -*- coding: utf-8 -*-
"""Sao luu NGUYEN trang 2 tab Lane-P / Lane-GEO (A:S + trang thai vang cot K) truoc khi ghi.
   py -3.13 scratch_analysis/snapshot_tabs.py <duong_dan_json>
"""
import sys, os, json, datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
os.environ.pop("PYTHONPATH", None)
import daily_sheet as dsh

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    "reports", f"backup_sheet_P_GEO_{datetime.date.today().isoformat()}_truoc_markK.json")
s = dsh.svc()
data = {}
for tab in ("Lane-P", "Lane-GEO"):
    rows, yel = dsh.read_tab(s, tab)
    data[tab] = {"rows": rows, "k_yellow": {str(k): v for k, v in yel.items() if v}}
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("da luu", os.path.abspath(out))
print({t: (len(v["rows"]), sum(1 for x in v["k_yellow"].values() if x)) for t, v in data.items()})
