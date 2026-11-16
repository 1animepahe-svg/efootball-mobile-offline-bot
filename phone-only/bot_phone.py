#!/usr/bin/env python3
"""
eFootball Mobile - Phone-only Offline Practice Bot (vs AI only)
Samsung Galaxy S21+ / Termux + wireless ADB.

No OpenCV: Pillow + numpy only, so it installs easily in Termux.
Reads the screen via local ADB, taps buttons via local ADB.
No game files touched, no anti-cheat bypass, no online play.
"""
import argparse
import io
import subprocess
import sys
import time

import numpy as np
import yaml
from PIL import Image


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def adb(*args):
    return subprocess.run(["adb", *args], capture_output=True, check=False)


def screenshot():
    """Return the screen as a numpy RGB array, or None."""
    p = subprocess.run(["adb", "exec-out", "screencap", "-p"],
                       capture_output=True, check=False)
    if not p.stdout:
        return None
    try:
        img = Image.open(io.BytesIO(p.stdout)).convert("RGB")
        return np.array(img)
    except Exception:
        return None


def tap(x, y):
    adb("shell", "input", "tap", str(int(x)), str(int(y)))


def swipe(x1, y1, x2, y2, ms=200):
    adb("shell", "input", "swipe",
        str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms)))


def detect_ball(frame, cfg):
    """Bright-spot heuristic. Returns (x, y) or None."""
    h, w = frame.shape[:2]
    top = int(h * cfg["detect"]["play_top_frac"])
    bottom = int(h * cfg["detect"]["play_bottom_frac"])
    crop = frame[top:bottom]
    # Brightness = max channel; ball is near-white
    bright = crop.max(axis=2)
    mask = bright > cfg["detect"]["ball_brightness"]
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    # Take the largest bright cluster roughly: use the median of
    # the brightest region by splitting the screen into a grid.
    # Simple version: centroid of all bright pixels, filtered to
    # the densest 100x100 block.
    best = None
    best_n = 0
    step = 100
    for gy in range(top, bottom, step):
        for gx in range(0, w, step):
            n = int(((xs >= gx) & (xs < gx + step) &
                     (ys >= gy - top) & (ys < gy - top + step)).sum())
            if n > best_n:
                sel = (xs >= gx) & (xs < gx + step) & \
                      (ys >= gy - top) & (ys < gy - top + step)
                if sel.sum() > cfg["detect"]["ball_min_area"]:
                    best_n = n
                    best = (int(xs[sel].mean()), int(ys[sel].mean()) + top)
    return best


def decide(frame, ball, cfg):
    if ball is None:
        return "switch"
    h, w = frame.shape[:2]
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

    print("Phone-only bot running — offline vs AI only. Ctrl+C to stop.")
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
