"""cc.py — launcher: py -3.13 E:\\CLAUDE\\YOUTUBE\\PHAN_TICH_TOI_UU_VIDEO\\comment_care\\cc.py run --channel F --mode draft_only"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from comment_care.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
