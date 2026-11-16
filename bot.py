#!/usr/bin/env python3
"""
eFootball Mobile - Offline Practice Bot (vs AI only)

Reads the screen via ADB, decides with OpenCV, presses on-screen
buttons via ADB. No game files are touched, no anti-cheat bypass,
no online play.
"""
import argparse
import subprocess
import sys
import time

import cv2
import numpy as np
import yaml


def load_config(path="config.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def adb(*args):
    return subprocess.run(["adb", *args], capture_output=True, check=False)


def screenshot():
    """Return the current phone screen as a BGR numpy array, or None."""
    p = subprocess.run(
        ["adb", "exec-out", "screencap", "-p"],
        capture_output=True, check=False,
    )
    if not p.stdout:
        return None
    img = cv2.imdecode(np.frombuffer(p.stdout, np.uint8), cv2.IMREAD_COLOR)
    return img


def tap(x, y):
    adb("shell", "input", "tap", str(int(x)), str(int(y)))


def swipe(x1, y1, x2, y2, ms=200):
    adb("shell", "input", "swipe",
        str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms)))


def detect_ball(frame, cfg):
    """
    Heuristic only: the ball is small, bright and roughly circular.
    Returns (x, y) in screen pixels, or None.
    Tune thresholds in config.yaml for your phone / stadium lighting.
    """
    h, w = frame.shape[:2]
    # Play area: ignore the top HUD and bottom buttons
    top = int(h * cfg["detect"]["play_top_frac"])
    bottom = int(h * cfg["detect"]["play_bottom_frac"])
    crop = frame[top:bottom]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(
        gray, cfg["detect"]["ball_brightness"], 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    best_area = 0
    for c in contours:
        area = cv2.contourArea(c)
        if cfg["detect"]["ball_min_area"] < area < cfg["detect"]["ball_max_area"]:
            if area > best_area:
                m = cv2.moments(c)
                if m["m00"]:
                    best = (int(m["m10"] / m["m00"]),
                            int(m["m01"] / m["m00"]) + top)
                    best_area = area
    return best


def decide(frame, ball, cfg):
    """Very simple state machine. Returns an action name."""
    if ball is None:
        return "switch"
    h, w = frame.shape[:2]
    bx, by = ball
    # Attacking to the right in this layout; flip if your match is reversed.
    if bx > w * cfg["decide"]["shoot_x_frac"]:
        return "shoot"
    if bx > w * cfg["decide"]["pass_x_frac"]:
        return "pass"
    return "dribble"


def do_action(action, cfg, frame):
    btn = cfg["buttons"]
    if action == "shoot":
        tap(*btn["shoot"])
    elif action == "pass":
        tap(*btn["pass"])
    elif action == "switch":
        tap(*btn["switch"])
    elif action == "dribble":
        # Hold sprint and push the joystick forward (right)
        joy = btn["joystick_center"]
        swipe(joy[0], joy[1], joy[0] + cfg["buttons"]["joystick_push_px"],
              joy[1], ms=cfg["timings"]["dribble_ms"])
        tap(*btn["sprint"])
    time.sleep(cfg["timings"]["action_delay_s"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print decisions, do not tap the screen")
    ap.add_argument("--seconds", type=float, default=0,
                    help="Stop after N seconds (0 = run until Ctrl+C)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    print("Checking ADB...")
    r = adb("devices")
    print(r.stdout.decode(errors="ignore"))
    if b"device" not in r.stdout:
        print("No phone found. Enable USB debugging and run: adb devices",
              file=sys.stderr)
        return 1

    print("Bot running — offline vs AI only. Ctrl+C to stop.")
    start = time.time()
    try:
        while True:
            if args.seconds and time.time() - start > args.seconds:
                break
            frame = screenshot()
            if frame is None:
                print("Could not grab a screenshot, retrying...")
                time.sleep(1)
                continue
            ball = detect_ball(frame, cfg)
            action = decide(frame, ball, cfg)
            print(f"ball={ball} action={action}")
            if not args.dry_run:
                do_action(action, cfg, frame)
            time.sleep(cfg["timings"]["loop_delay_s"])
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
