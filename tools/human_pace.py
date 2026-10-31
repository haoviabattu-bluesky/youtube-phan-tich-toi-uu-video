# -*- coding: utf-8 -*-
r"""
NHIP DO "NHU NGUOI THAT" cho cac tool doc YouTube Studio.

VI SAO CO FILE NAY (do that tu log 2026-10-19/2026-10-20):
  Job 05:00 doc 3 trang Studio cho moi video (overview -> bam Reach -> period 24h), moi trang
  chi dung ~4s roi nhay tiep => median 13,5s/video, co video 0s. Studio phan ung bang
  "Oops, something went wrong" — lane A (5 video lien tiep) mat 457s/video ma KHONG doc duoc so
  nao. Nguoi that mo 1 trang analytics mat 20-40s (doc so, cuon chuot, nhin bieu do), va giua
  2 video con lam viec khac.

CACH DUNG:
  import human_pace as hp
  hp.before_nav(log)      # truoc khi mo trang moi
  hp.before_click(log)    # truoc khi bam tab
  hp.after_read(log)      # doc xong so -> dung lai "doc" them
  hp.wander(page, log)    # cu dong chuot + cuon nhe
  hp.between_videos(log)  # giua 2 video
  hp.session_break(log)   # nghi dai sau N video
  hp.after_oops(log)      # Studio bao loi -> doi LAU roi moi thu lai

TAT NHANH (dung khi test/do thoi gian): dat HUMAN_PACE=0 trong moi truong.
"""
import os, random, time

_ON = os.environ.get("HUMAN_PACE", "1") not in ("0", "false", "False", "no")
try:
    _SCALE = float(os.environ.get("HUMAN_PACE_SCALE", "1") or 1)
except ValueError:
    _SCALE = 1.0


def on():
    return _ON


def set_on(flag):
    """Bat/tat bang code (vd co --fast). Phai goi TRUOC khi cac module khac doc _ON."""
    global _ON
    _ON = bool(flag)


def pause(a, b, why="", log=None):
    """Nghi ngau nhien [a,b] giay (nhan HUMAN_PACE_SCALE). Tra so giay da nghi."""
    if not _ON:
        return 0.0
    t = random.uniform(a, b) * _SCALE
    if log and why:
        log(f"    · {why}: nghi {t:.1f}s")
    time.sleep(t)
    return t


# ---- cac moc trong 1 video (so do tu cach nguoi that xem Studio) ----
def before_nav(log=None):
    pause(2.5, 6.5, "mo trang", log)


def before_click(log=None):
    pause(1.2, 3.5, "truoc khi bam tab", log)


def after_read(log=None):
    pause(1.5, 4.5, "doc so xong", log)


def between_videos(log=None):
    pause(20.0, 55.0, "chuyen video", log)


def session_break(log=None):
    pause(90.0, 240.0, "nghi giua phien", log)


def after_oops(log=None):
    pause(45.0, 120.0, "Studio bao loi, doi lau", log)


def wander(page, log=None):
    """Cu dong chuot + cuon nhe nhu nguoi dang doc so lieu (khong lam hong gi)."""
    if not _ON:
        return
    try:
        for _ in range(random.randint(1, 3)):
            page.mouse.move(random.randint(200, 1100), random.randint(150, 700),
                            steps=random.randint(6, 18))
            time.sleep(random.uniform(0.2, 0.6))
        if random.random() < 0.5:
            page.mouse.wheel(0, random.randint(120, 420))
            time.sleep(random.uniform(0.4, 1.2))
            page.mouse.wheel(0, -random.randint(80, 300))
    except Exception:
        pass   # trang dang chuyen / khong co chuot -> khong sao
