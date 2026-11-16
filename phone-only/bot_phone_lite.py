#!/usr/bin/env python3
"""
eFootball Mobile - Phone-only Offline Practice Bot, LITE version (vs AI only)
No numpy, no OpenCV — Pillow + yaml only.

Use this if numpy fails to import in Termux with:
  dlopen failed: cannot locate symbol "_ZNSt6__ndk113__hash_memoryEPKvm"
That is the pip-built numpy wheel being incompatible with Termux's
Python 3.14 / libc++. This lite bot avoids numpy entirely.
"""
import argparse
import io
import subprocess
import sys
import time

import yaml
from PIL import Image


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def adb(*args):
    return subprocess.run(["adb", *args], capture_output=True, check=False)


def screenshot():
    """Return the screen as a PIL RGB image, or None."""
    p = subprocess.run(["adb", "exec-out", "screencap", "-p"],
                       capture_output=True, check=False)
    if not p.stdout:
        return None
    try:
        return Image.open(io.BytesIO(p.stdout)).convert("RGB")
    except Exception:
        return None


def tap(x, y):
    adb("shell", "input", "tap", str(int(x)), str(int(y)))


def swipe(x1, y1, x2, y2, ms=200):
    adb("shell", "input", "swipe",
        str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms)))


def detect_ball(img, cfg):
    """Bright-spot heuristic, Pillow only. Returns (x, y) or None."""
    w, h = img.size
    # Downscale for speed: 270 px wide is enough to find the ball.
    scale = 270 / w
    small = img.resize((270, int(h * scale)))
    sw, sh = small.size
    top = int(sh * cfg["detect"]["play_top_frac"])
    bottom = int(sh * cfg["detect"]["play_bottom_frac"])
    px = small.load()
    thresh = cfg["detect"]["ball_brightness"]
    # Grid 27 x 27 px cells, count bright pixels per cell.
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
    ap.add_argument("--config", default="../config.yaml")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seconds", type=float, default=0)
    args = ap.parse_args()

    cfg = load_config(args.config)
    r = adb("devices")
    print(r.stdout.decode(errors="ignore"))
    if b"\tdevice" not in r.stdout:
        print("No ADB device. Run bash run.sh first to pair/connect.",
              file=sys.stderr)
        return 1

    print("Phone-only LITE bot running — offline vs AI only. Ctrl+C to stop.")
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
