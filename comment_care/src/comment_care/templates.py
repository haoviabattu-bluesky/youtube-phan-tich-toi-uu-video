"""templates.py — thư viện câu có kiểm soát + footer (spec mục H/M)."""
import random
import re
from pathlib import Path

import yaml


class Templates:
    def __init__(self, path: Path, seed=None):
        self.t = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        self.slots = self.t["slots"]
        self.rng = random.Random(seed)

    def hostile(self) -> str:
        return self.t["by_category"]["HOSTILE"]["fixed"]

    def render(self, category: str, detail: str = "", avoid_combos=()) -> tuple[str, str]:
        """→ (text, combo_key). Tránh lặp tổ hợp slot với `avoid_combos` (20 reply gần nhất cùng video)."""
        spec = self.t["by_category"].get(category)
        if not spec:
            raise KeyError(f"không có template cho {category}")
        if "fixed" in spec:
            return spec["fixed"], f"{category}:fixed"
        pattern = spec["pattern"]
        names = re.findall(r"\{(\w+)\}", pattern)
        best = None
        for _ in range(30):
            pick = {}
            for n in names:
                if n == "detail_clause":
                    d = (detail or "").strip().rstrip("。")
                    # chỉ chèn khi detail là góp ý về CÁCH LÀM video (giọng/chữ/độ dài/BGM…), không chèn fact của câu chuyện
                    ok = bool(d) and bool(re.search(r"音声|音量|声|BGM|字幕|テロップ|文字|長さ|長い|短い|速|テンポ|画|絵|タイトル|サムネ|構成|説明|聞き取り", d))
                    pick[n] = spec.get("detail_clause", "").replace("{detail}", d) if ok else ""
                elif n in self.slots:
                    pick[n] = self.rng.choice(self.slots[n])
                else:
                    pick[n] = ""
            combo = category + ":" + "|".join(str(self.slots[n].index(pick[n])) if n in self.slots else "-" for n in names)
            text = pattern
            for n, v in pick.items():
                text = text.replace("{" + n + "}", v)
            if combo not in avoid_combos:
                return text, combo
            best = best or (text, combo)
        return best

    # ------------------------------------------------------------ footer
    def footer(self, footer_policy: str, footer_rule: str, video_id: str, first_reply_of_video: bool) -> str:
        """footer_policy A/B/C/BC × footer_rule yes/no → chuỗi footer ('' nếu không gắn)."""
        f = self.t["footer"]
        if footer_policy in ("B", "BC") and footer_rule != "yes":
            return ""
        if footer_policy == "A":
            return f["full"]
        if footer_policy == "B":
            return f["full"]
        # C / BC: rotate theo video; bản đầy đủ chỉ cho reply đầu tiên của video
        if first_reply_of_video:
            return f["full"]
        vs = f["variants"]
        idx = sum(ord(ch) for ch in video_id) % len(vs)
        return vs[idx]

    def all_footer_texts(self):
        f = self.t["footer"]
        return [f["full"]] + list(f["variants"])
