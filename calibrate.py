#!/usr/bin/env python3
"""
Calibrate button positions for your phone.

1. Open eFootball Mobile, start an offline match vs AI.
2. Run: python calibrate.py
3. For each button name, tap that button on the phone screen.
   This script reads the last touch position via `adb shell getevent`
   is unreliable across devices, so instead it asks you to type the
   coordinates — find them by enabling Developer Options >
   "Pointer location" on the phone, which shows x,y as you touch.

Simpler alternative: take a screenshot, open it, and read the
button centres in an image editor, then paste them here.
"""
import subprocess

import yaml

BUTTONS = ["pass", "shoot", "through", "sprint", "switch",
           "joystick_center"]


def screen_size():
    p = subprocess.run(["adb", "shell", "wm", "size"],
                       capture_output=True, text=True)
    print(p.stdout.strip())
    return p.stdout.strip()


def main():
    print("Phone screen:", screen_size())
    print("Open an offline match, turn on Pointer location in "
          "Developer Options, and note x,y for each button.\n")
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    for name in BUTTONS:
        cur = cfg["buttons"][name]
        raw = input(f"{name}  [current {cur}]  x,y (Enter to keep): ").strip()
        if raw:
            x, y = raw.replace(" ", "").split(",")
            cfg["buttons"][name] = [int(x), int(y)]
    with open("config.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)
    print("Saved to config.yaml")


if __name__ == "__main__":
    main()
