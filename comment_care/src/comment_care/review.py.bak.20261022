"""review.py — đọc DRAFT_REVIEW.txt anh đã ghi `YOUR_DECISION:` và áp vào DB (APPROVE / EDIT: <text> / REJECT / SKIP)."""
import re
from pathlib import Path

BLOCK = re.compile(r"DRAFT_ID:\s*(\d+)(.*?)YOUR_DECISION:\s*([^\n]*)", re.S)


def parse(path: Path) -> list[tuple[int, str, str | None]]:
    out = []
    for m in BLOCK.finditer(Path(path).read_text(encoding="utf-8")):
        did, raw = int(m.group(1)), m.group(3).strip()
        if not raw:
            continue
        up = raw.upper()
        if up.startswith("APPROVE"):
            out.append((did, "APPROVE", None))
        elif up.startswith("EDIT"):
            txt = raw.split(":", 1)[1].strip() if ":" in raw else ""
            # cho phép câu sửa nằm ở các dòng tiếp theo trước dấu ----
            out.append((did, "EDIT", txt or None))
        elif up.startswith("REJECT"):
            out.append((did, "REJECT", None))
        elif up.startswith("SKIP"):
            out.append((did, "SKIP", None))
    return out


def apply(store, path: Path) -> list[str]:
    log = []
    for did, dec, txt in parse(path):
        try:
            st = store.review_apply(did, dec, edited_text=txt)
            log.append(f"draft {did}: {dec} → {st}")
        except KeyError as e:
            log.append(f"draft {did}: lỗi {e}")
    return log
