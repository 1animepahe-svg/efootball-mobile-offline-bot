# eFootball Mobile — Offline Practice Bot

An automation starter for **offline matches vs the AI only, on Android**.

It does NOT mod the game, does NOT touch game files, does NOT bypass
anti-cheat, and must NOT be used in online matches. Online use would
cheat other players, break Konami's terms, and risk a ban.

How it works:
- Your PC talks to your phone over ADB (USB debugging)
- The bot grabs the screen with `adb screencap`
- OpenCV looks for the ball / your player marker and decides
  pass / shoot / sprint / switch
- It presses the on-screen buttons with `adb input tap` / `swipe`

## What you need

- Android phone with eFootball Mobile installed
- A PC (Windows / Mac / Linux) with Python 3.10+
- USB cable, Developer Options > USB debugging ON
- eFootball set to Classic controls, offline match vs AI

## Setup

```bash
pip install -r requirements.txt
adb devices
# should list your phone, authorised
python calibrate.py
python bot.py
```

`calibrate.py` asks you to tap each button once on the phone screen
while the game is open. It saves the real coordinates to `config.yaml`
for your phone's resolution. The defaults in `config.yaml` are for
1080 x 2400 — do not trust them blindly, calibrate first.

## Files

- `bot.py` — main loop: screenshot, detect, decide, act
- `calibrate.py` — record button positions for your device
- `config.yaml` — resolution + button coordinates + timings
- `requirements.txt` — opencv-python, numpy, pyyaml

## How the bot decides (simple, honest version)

1. Find the ball: brightest white circle in the play area.
   This is a heuristic, not a game hack — it only reads pixels.
2. Find your controlled player: the marker above the player.
3. If the ball is near your goal and you have it, dribble forward.
4. If you are in the final third, shoot.
5. If a teammate is ahead, pass.
6. If you don't have the ball, sprint toward it and switch when needed.

It will not play like a human. It is a starter you can tune:
change the thresholds in `config.yaml`, add templates in
`templates/` (screenshots of the pass / shoot buttons), and
improve the detection in `bot.py:detect_ball()`.

## GitHub

```bash
git init
git add .
git commit -m "eFootball Mobile offline practice bot"
gh repo create efootball-mobile-offline-bot --public --source=. --push
```

## Safety

- Offline vs AI only.
- Stop the bot with Ctrl+C. It never runs in the background.
- If eFootball updates its UI, re-run `calibrate.py`.
