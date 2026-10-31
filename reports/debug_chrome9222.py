# -*- coding: utf-8 -*-
"""Debug: mo Chrome 9222 giong daily_profiles._open_9222 va xem no chet o dau."""
import sys, os, time, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from daily_profiles import CHROME, PROFILE_9222, DETACH, _alive

print("CHROME      :", CHROME, "| ton tai:", os.path.exists(CHROME))
print("PROFILE_9222:", PROFILE_9222, "| ton tai:", os.path.exists(PROFILE_9222))
print("dang co CDP 9222:", _alive("http://127.0.0.1:9222/json/version"))

cmd = [CHROME, f"--user-data-dir={PROFILE_9222}", "--remote-debugging-port=9222", "--no-first-run"]
print("\nchay:", " ".join(cmd))
p = subprocess.Popen(cmd, creationflags=DETACH, close_fds=True)
print("PID:", p.pid)

for i in range(20):
    time.sleep(1.5)
    alive = _alive("http://127.0.0.1:9222/json/version")
    code = p.poll()
    print(f"  {i*1.5:4.1f}s  CDP={alive}  proc_exit={code}")
    if alive:
        break
    if code is not None:
        print("  -> Chrome THOAT voi code", code)
        break

o = subprocess.run(["wmic", "process", "where", "name='chrome.exe'", "get", "ProcessId,CommandLine"],
                   capture_output=True, text=True).stdout
hits = [l for l in o.splitlines() if "HAOVIABATTU" in l or "9222" in l]
print("\nchrome co --user-data-dir HAOVIABATTU:", len(hits))
for h in hits[:3]:
    print("  ", h.strip()[:200])
