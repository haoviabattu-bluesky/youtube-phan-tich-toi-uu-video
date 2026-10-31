# -*- coding: utf-8 -*-
r"""
LUAT COT K + TO VANG (anh chot 2026-10-16, memory mark-column-k-yellow):
  CTR 24h >= 2,5%  -> K = "158h · 6.000 view · CTR tổng 4,7% · CTR 24h 4,4% · 589 lượt hiển thị/24h.
                          ĐỂ NGUYÊN (CTR 24h đạt, đang được phân phối)."   + bo vang (neu dong dang vang)
  CTR 24h < 2,5%   -> K = "CTR 24h=1,6%, YÊU CẦU THAY THUMB VÀ TIÊU ĐỀ"  + to vang CA DONG
  CTR 24h "—"      -> coi nhu < 2,5%: K = "CTR 24h=— (5 hiển thị), YÊU CẦU THAY THUMB VÀ TIÊU ĐỀ"
Ap cho MOI video (ke ca >1000 view, <48h). CTR 24h = cot Q vua do (24h truot now-24h..now).
"""
THRESHOLD = 2.5


def vn_int(n):
    return f"{int(n):,}".replace(",", ".") if n is not None else "—"


def vn_pct(v):
    return (f"{v:.1f}".replace(".", ",") + "%") if v is not None else "—"


def k_note(hours, views, ctr_total, ctr_24h, imp_24h):
    """Tra (chuoi K, to_vang: bool)."""
    if ctr_24h is None or ctr_24h < THRESHOLD:
        val = vn_pct(ctr_24h) if ctr_24h is not None else f"— ({vn_int(imp_24h or 0)} hiển thị)"
        return f"CTR 24h={val}, YÊU CẦU THAY THUMB VÀ TIÊU ĐỀ", True
    return (f"{int(hours)}h · {vn_int(views)} view · CTR tổng {vn_pct(ctr_total)} · CTR 24h {vn_pct(ctr_24h)}"
            f" · {vn_int(imp_24h)} lượt hiển thị/24h. ĐỂ NGUYÊN (CTR 24h đạt, đang được phân phối)."), False


if __name__ == "__main__":
    assert k_note(158.4, 6000, 4.7, 4.4, 589) == (
        "158h · 6.000 view · CTR tổng 4,7% · CTR 24h 4,4% · 589 lượt hiển thị/24h. "
        "ĐỂ NGUYÊN (CTR 24h đạt, đang được phân phối).", False)
    assert k_note(80, 300, 3.0, 1.6, 900) == ("CTR 24h=1,6%, YÊU CẦU THAY THUMB VÀ TIÊU ĐỀ", True)
    assert k_note(80, 300, 3.0, None, 5) == ("CTR 24h=— (5 hiển thị), YÊU CẦU THAY THUMB VÀ TIÊU ĐỀ", True)
    assert k_note(80, 300, 3.0, 2.5, 50)[1] is False
    print("k_rules OK")
