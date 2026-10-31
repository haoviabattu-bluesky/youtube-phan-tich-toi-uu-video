# -*- coding: utf-8 -*-
"""Test lock_take: khoa mo coi (PID da chet) phai bi bo NGAY, khong doi 15 phut."""
import sys, os, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "view_spike"))

LOCK = os.path.join(ROOT, "view_spike", "state", "run.lock")

# nap module daily_0500_run nhung KHONG chay main
import importlib.util
spec = importlib.util.spec_from_file_location("d5", os.path.join(ROOT, "tools", "daily_0500_run.py"))
d5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d5)

print("LOCK =", d5.spike_state.LOCK)

# 1. khoa mo coi: PID khong ton tai
open(d5.spike_state.LOCK, "w").write("999999 0")
t0 = time.time()
ok = d5.lock_take(wait_min=15)
dt = time.time() - t0
print(f"khoa mo coi -> lock_take={ok} sau {dt:.1f}s (ky vong < 2s)")
assert ok, "phai lay duoc khoa"
assert dt < 5, f"qua cham: {dt:.1f}s — van con cho 15 phut"
d5.spike_state.release_lock()

# 2. khoa cua tien trinh CON SONG -> phai tu cho (khong cuop)
open(d5.spike_state.LOCK, "w").write(f"{os.getpid()} {time.time()}")
t0 = time.time()
ok = d5.lock_take(wait_min=0)   # wait_min=0 -> thu 0 lan, tra False ngay
print(f"khoa dang song -> lock_take(wait_min=0)={ok} sau {time.time()-t0:.1f}s (ky vong False)")
assert ok is False
os.remove(d5.spike_state.LOCK)
print("ALL PASS")
