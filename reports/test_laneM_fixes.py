# -*- coding: utf-8 -*-
"""Unit test cho 2 lo fix 2026-10-18 (khong can Chrome):
  1. studio_daily.report_end_day khop nhan ngay co U+2009 thin space
  2. studio_collect: khoi 'YouTube search terms' KHONG du du lieu -> khong doc nham 'Browse features'
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import studio_daily as sd


def parse_search_term(parts):
    """Ban sao logic trong collect_video (de test duoc khong can browser)."""
    try:
        i = parts.index("YouTube search terms")
        seg = parts[i:i + 30]
        k0 = seg.index("Proportion of your total traffic:")
        end = next((j for j in range(k0, len(seg)) if seg[j].strip() == "See more"), len(seg))
        if any(t.startswith("Not enough traffic data") for t in seg[k0:end]):
            raise ValueError
        k = k0
        term, pct = "", ""
        for a in range(k + 2, len(seg) - 1):
            if not seg[a].endswith("%") and seg[a + 1].endswith("%") and seg[a] != "See more":
                term, pct = seg[a][:60], seg[a + 1]
                break
        return term, pct
    except ValueError:
        return "", ""


# --- 1. nhan ngay
cases = {
    "Sep 19\u2009–\u2009Oct 16, 2026": "2026-10-16",   # Studio that (thin space U+2009)
    "Sep 14 – 22, 2026": "2026-09-22",                  # cung thang
    "Aug 26 – Sep 22, 2026": "2026-09-22",              # khac thang
    "Sep 19 – Oct 16, 2026": "2026-10-16",              # space thuong
}
for label, expect in cases.items():
    got = sd.report_end_day([label])
    assert str(got) == expect, f"report_end_day({label!r}) = {got}, ky vong {expect}"
    print(f"OK report_end_day {label!r} -> {got}")

# --- 2. search terms khong du du lieu (dinh that ep07)
not_enough = ["YouTube search terms", "The YouTube search terms that brought viewers to your video.",
              "Views · Since published", "Proportion of your total traffic:", "0.2%",
              "Not enough traffic data to show this report", "See more",
              "Browse features", "57.1%"]
term, pct = parse_search_term(not_enough)
assert (term, pct) == ("", ""), f"phai rong, nhan duoc {term!r} {pct!r}"
print("OK search-term rong khi 'Not enough traffic data' ->", (term, pct))

# --- 3. search terms CO du lieu (ep01) van doc dung
enough = ["YouTube search terms", "desc", "Views · Since published", "Proportion of your total traffic:",
          "1.5%", "シルバー人材センター", "4.0%", "See more", "Browse features", "62.7%"]
term, pct = parse_search_term(enough)
assert (term, pct) == ("シルバー人材センター", "4.0%"), f"nhan duoc {term!r} {pct!r}"
print("OK search-term doc dung ->", (term, pct))
print("ALL PASS")
