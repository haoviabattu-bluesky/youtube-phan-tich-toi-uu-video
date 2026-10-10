"""context.py — ĐỌC HIỂU VIDEO trước khi trả lời (yêu cầu anh 2026-10-05): title/description từ API + thư mục tập của h2dev.

Thứ tự tìm thư mục tập cho 1 video_id:
  1. Google Sheet tab lane: cột L (video_id) → cột C (FOLDER = thư mục assets của tập)   [chính xác nhất]
  2. Khớp tiêu đề: dòng 1 của `TIEU_DE_MO_TA.txt` / `title.txt` trong assets_dir hoặc FlowHandoff_local\\jobs\\<tab>\\*
Mức context: L3 = có thư mục assets (S1_TOM_TAT/promise/story_facts) · L3J = chỉ có jobs (dan_y/script head) · L1 = chỉ title+description API · NONE.
Không bao giờ nạp full script: tối đa ~2.300 ký tự đưa vào prompt.
"""
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

_SHEET_CACHE: dict[str, dict] = {}


@dataclass
class VideoContext:
    video_id: str
    title: str = ""
    description_head: str = ""
    ep_dir: str | None = None
    level: str = "NONE"
    summary_ja: str = ""
    key_points: list = field(default_factory=list)
    spoilers: list = field(default_factory=list)
    characters: list = field(default_factory=list)
    promise: str = ""
    outline_head: str = ""
    emotion: str = ""

    def to_json(self):
        return json.dumps(asdict(self), ensure_ascii=False)

    def to_prompt_text(self, max_chars=2300):
        parts = [f"タイトル: {self.title}"]
        if self.description_head:
            parts.append("説明文(冒頭): " + self.description_head[:500])
        if self.promise:
            parts.append("動画の約束(要点): " + self.promise[:200])
        if self.summary_ja:
            parts.append("あらすじ: " + self.summary_ja[:700])
        if self.key_points:
            parts.append("伝えたいこと: " + " / ".join(k[:80] for k in self.key_points[:4]))
        if self.characters:
            parts.append("登場人物: " + "、".join(self.characters[:5]))
        if self.emotion:
            parts.append("感情の軸: " + self.emotion[:120])
        if self.outline_head and not self.summary_ja:
            parts.append("構成(冒頭): " + self.outline_head[:600])
        if self.spoilers:
            parts.append("言ってはいけないこと(ネタバレ・誤解): " + " / ".join(s[:80] for s in self.spoilers[:4]))
        return "\n".join(parts)[:max_chars]


def _read(p: Path, n=None):
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
        return t[:n] if n else t
    except OSError:
        return ""


def sheet_folder_map(sheet_id, tab, sa_path, col_folder=2, col_id=11) -> dict:
    """{video_id: folder} từ tab lane. Lỗi → {} (fallback khớp tiêu đề)."""
    if tab in _SHEET_CACHE:
        return _SHEET_CACHE[tab]
    m = {}
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        creds = Credentials.from_service_account_file(sa_path, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
        svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
        rows = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"{tab}!A2:L300").execute().get("values", [])
        for r in rows:
            vid = r[col_id].strip() if len(r) > col_id else ""
            fol = r[col_folder].strip() if len(r) > col_folder else ""
            if re.fullmatch(r"[A-Za-z0-9_-]{11}", vid) and fol:
                m[vid] = fol
    except Exception as e:  # noqa: BLE001 — sheet chỉ là đường tắt, không được làm chết run
        print(f"  ! sheet map {tab}: {type(e).__name__} {str(e)[:120]}")
    _SHEET_CACHE[tab] = m
    return m


def _first_line(p: Path):
    t = _read(p, 400).strip()
    return t.splitlines()[0].strip() if t else ""


def _norm_title(t):
    return re.sub(r"[\s【】\[\]「」『』…・、。,.!?！？\-—–]", "", t or "")


def find_by_title(title, dirs: list[Path]):
    want = _norm_title(title)
    if not want:
        return None
    for base in dirs:
        if not base or not base.exists():
            continue
        for d in sorted(base.iterdir()):
            if not d.is_dir():
                continue
            for f in ("TIEU_DE_MO_TA.txt", "title.txt"):
                got = _norm_title(_first_line(d / f))
                if got and (got == want or got[:25] == want[:25]):
                    return d
    return None


def build(video_row: dict, ch, settings) -> VideoContext:
    vc = VideoContext(video_id=video_row["video_id"], title=video_row.get("title") or "",
                      description_head=(video_row.get("description_head") or "")[:600])
    if vc.title:
        vc.level = "L1"
    tab = ch.sheet_tab
    ep = None
    if tab:
        fol = sheet_folder_map(settings["sheet"]["id"], tab, settings["paths"]["sheets_service_account"],
                               settings["sheet"]["col_folder"], settings["sheet"]["col_video_id"]).get(vc.video_id)
        if fol and Path(fol).exists():
            ep = Path(fol)
    if ep is None:
        cands = []
        if ch.h2dev_assets_dir:
            cands.append(Path(ch.h2dev_assets_dir))
        if tab:
            cands.append(Path(settings["paths"]["flowhandoff_jobs"]) / tab)
        ep = find_by_title(vc.title, cands)
    if ep is None:
        return vc
    vc.ep_dir = str(ep)
    # ---- assets-level files
    s1 = ep / "research" / "S1_TOM_TAT.json"
    if s1.exists():
        try:
            d = json.loads(_read(s1))
            vc.summary_ja = str(d.get("tom_tat", ""))
            vc.key_points = [str(x) for x in (d.get("y_chinh") or [])]
            vc.spoilers = [str(x) for x in (d.get("khong_duoc_noi_qua") or [])]
            vc.emotion = str(d.get("cam_xuc_dinh", ""))
            nv = d.get("nhan_vat") or {}
            if isinstance(nv, dict) and nv.get("nguoi_ke"):
                vc.characters.append(str(nv["nguoi_ke"])[:80])
        except (ValueError, TypeError):
            pass
    sf = ep / "story_facts.json"
    if sf.exists() and not vc.characters:
        try:
            chs = json.loads(_read(sf)).get("characters") or {}
            vc.characters = [f"{n}({v.get('age')}歳)" if isinstance(v, dict) and v.get("age") else n for n, v in list(chs.items())[:5]]
        except (ValueError, TypeError, AttributeError):
            pass
    vc.promise = _read(ep / "promise.txt", 300).strip()
    tdm = _read(ep / "TIEU_DE_MO_TA.txt", 1500).strip()
    if tdm and not vc.description_head:
        vc.description_head = tdm[:600]
    if not vc.title:
        vc.title = _first_line(ep / "title.txt") or _first_line(ep / "TIEU_DE_MO_TA.txt")
    if vc.summary_ja or vc.promise or vc.key_points:
        vc.level = "L3"
    else:
        dy = _read(ep / "dan_y.txt", 900).strip()
        sc = _read(ep / "script.txt", 900).strip()
        vc.outline_head = dy or sc
        vc.level = "L3J" if vc.outline_head else ("L1" if vc.title else "NONE")
    return vc
