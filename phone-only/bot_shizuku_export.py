#!/usr/bin/env python3
"""
eFootball Mobile - Shizuku / rish version (vs AI only, offline)
No numpy, no adb connect, no Wi-Fi needed once Shizuku is running.

Setup:
  1. Install Shizuku (Play Store, by Rikka), start it via Wireless
     debugging (split-screen pairing, once per reboot).
     Shizuku must say Running before rish will work.
  2. Get rish from Shizuku itself — it is NOT a Termux package,
     `pkg install rish` fails, and https://rikka.app/rish/latest
     returns a web page, not the script. In the Shizuku app tap
     "Use Shizuku in terminal apps" > "Export files", save the
     two files `rish` and `rish_shizuku.dex`, then in Termux:
       termux-setup-storage
       cp ~/storage/downloads/rish ~/storage/downloads/rish_shizuku.dex $PREFIX/bin/
       chmod +x $PREFIX/bin/rish
     Keep both files together in the same folder. If the exported
     `rish` file still contains the word PKG, edit it to
     com.termux. Test with:
       export RISH_APPLICATION_ID=com.termux
       rish -c "id"   -- should show uid=2000(shell)
     (If you copied rish to ~/ instead, this bot also looks for
     ~/rish, but $PREFIX/bin is the reliable place — it is on PATH.)
  3. Run this bot from ~/efootball-bot:
       python bot_shizuku.py --config config.yaml
"""
import argparse
import io
import os
import shutil
import subprocess
import sys
import time

import yaml
from PIL import Image


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_rish():
    """Locate the rish launcher: PATH first, then $PREFIX/bin, then ~/rish."""
    for cand in (shutil.which("rish"),
                 os.path.join(os.environ.get("PREFIX", ""), "bin", "rish"),
                 os.path.expanduser("~/rish"),
                 os.path.join(os.getcwd(), "rish")):
        if cand and os.path.isfile(cand):
            return cand
    return None


RISH = find_rish()


def rish_env():
    env = dict(os.environ)
    # Termux's package id; the exported rish script needs it to find
    # the right app. Harmless if the script already has it baked in.
    env.setdefault("RISH_APPLICATION_ID", "com.termux")
    return env


def rish(*args):
    if RISH is None:
        raise FileNotFoundError(
            "rish not found. Export it from Shizuku ('Use Shizuku in "
            "terminal apps' > 'Export files'), copy rish + "
            "rish_shizuku.dex to $PREFIX/bin/, chmod +x $PREFIX/bin/rish, "
            "then test: rish -c \"id\"")
    return subprocess.run([RISH, "-c", " ".join(args)],
                          capture_output=True, check=False, env=rish_env())


def screenshot():
    p = rish("screencap", "-p")
    if not p.stdout:
        return None
    try:
        return Image.open(io.BytesIO(p.stdout)).convert("RGB")
    except Exception:
        return None


def tap(x, y):
    rish("input", "tap", str(int(x)), str(int(y)))


def swipe(x1, y1, x2, y2, ms=200):
    rish("input", "swipe", str(int(x1)), str(int(y1)),
         str(int(x2)), str(int(y2)), str(int(ms)))


def detect_ball(img, cfg):
    w, h = img.size
    scale = 270 / w
    small = img.resize((270, int(h * scale)))
    sw, sh = small.size
    top = int(sh * cfg["detect"]["play_top_frac"])
    bottom = int(sh * cfg["detect"]["play_bottom_frac"])
    px = small.load()
    thresh = cfg["detect"]["ball_brightness"]
    cell = 27
    best = None
    best_n = 0
    for gy in range(top, bottom, cell):
        for gx in range(0, sw, cell):
            n = 0
            sx = 0
            sy = 0
            for y in range(gy, min(gy + cell, bottom), 3):
                for x in range(gx, min(gx + cell, sw), 3):
                    r, g, b = px[x, y]
                    if r > thresh and g > thresh and b > thresh:
                        n += 1
                        sx += x
                        sy += y
            if n > best_n and n >= 2:
                best_n = n
                best = (int(sx / n / scale), int(sy / n / scale))
    return best


def decide(img, ball, cfg):
    if ball is None:
        return "switch"
    w, _ = img.size
    bx, _ = ball
    if bx > w * cfg["decide"]["shoot_x_frac"]:
        return "shoot"
    if bx > w * cfg["decide"]["pass_x_frac"]:
        return "pass"
    return "dribble"


def do_action(action, cfg):
    btn = cfg["buttons"]
    if action == "shoot":
        tap(*btn["shoot"])
    elif action == "pass":
        tap(*btn["pass"])
    elif action == "switch":
        tap(*btn["switch"])
    elif action == "dribble":
        joy = btn["joystick_center"]
        swipe(joy[0], joy[1], joy[0] + cfg["buttons"]["joystick_push_px"],
              joy[1], ms=cfg["timings"]["dribble_ms"])
        tap(*btn["sprint"])
    time.sleep(cfg["timings"]["action_delay_s"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seconds", type=float, default=0)
    args = ap.parse_args()

    cfg = load_config(args.config)
    if RISH is None:
        print("rish not found, and Shizuku alone is not enough — the bot "
              "needs the rish launcher.", file=sys.stderr)
        print("In Shizuku: 'Use Shizuku in terminal apps' > 'Export files', "
              "then in Termux:", file=sys.stderr)
        print("  cp ~/storage/downloads/rish "
              "~/storage/downloads/rish_shizuku.dex $PREFIX/bin/", file=sys.stderr)
        print("  chmod +x $PREFIX/bin/rish", file=sys.stderr)
        print("  rish -c \"id\"   # should show uid=2000(shell)", file=sys.stderr)
        return 1
    try:
        r = rish("id")
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(r.stdout.decode(errors="ignore"))
    if b"uid=2000" not in r.stdout:
        print("rish ran but Shizuku is not running (no uid=2000). "
              "Start Shizuku first — it must say Running — then retry: "
              "rish -c \"id\"", file=sys.stderr)
        return 1

    print("Shizuku bot running — offline vs AI only. Ctrl+C to stop.")
    start = time.time()
    try:
        while True:
            if args.seconds and time.time() - start > args.seconds:
                break
            frame = screenshot()
            if frame is None:
                time.sleep(1)
                continue
            ball = detect_ball(frame, cfg)
            action = decide(frame, ball, cfg)
            print(f"ball={ball} action={action}", flush=True)
            if not args.dry_run:
                do_action(action, cfg)
            time.sleep(cfg["timings"]["loop_delay_s"])
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
