# Phone-only version — Samsung Galaxy S21+, no PC

Runs entirely on your S21+. No PC, no USB cable after setup.

It uses **Termux + wireless ADB**. Your phone talks to itself:
Termux runs the bot, ADB (wireless debugging) grabs the screen
and taps the buttons. Same rules as before: **offline vs AI only**,
no game modding, no anti-cheat bypass, no online matches.

## 1. Install Termux (important: use F-Droid, not Play Store)

Play Store Termux is old and broken. Get it from F-Droid:
https://f-droid.org/packages/com.termux/

Install that APK, open Termux.

## 2. Turn on wireless debugging

Settings > Developer options > Wireless debugging > ON

If you don't see Developer options:
Settings > About phone > Software information > tap
"Build number" 7 times.

## 3. Install the bot in Termux

In Termux, run:

```bash
bash setup_termux.sh
```

That installs Python, ADB, Pillow and numpy, and copies the
bot files. First run takes a few minutes — let it finish.

Or do it by hand:

```bash
pkg update && pkg install -y python android-tools
pip install pillow numpy pyyaml
```

Then copy `bot_phone.py` and `../config.yaml` into Termux
home (`~/efootball-bot/`).

## 4. Pair wireless ADB (do this once per reboot)

In Settings > Developer options > Wireless debugging,
tap "Pair device with pairing code". Note the IP, port
and 6-digit code, e.g. `192.168.1.5:45671`, code `123456`.

In Termux:

```bash
adb pair 192.168.1.5:45671 123456
adb connect 192.168.1.5:37123
adb devices
```

The connect port is different from the pair port — it is
shown on the Wireless debugging screen after pairing.
`run.sh` will ask you for both and do this for you.

## 5. Play

1. Open eFootball, start an offline match vs AI, Classic controls.
2. Switch back to Termux (don't close eFootball).
3. Run:

```bash
bash run.sh
```

Or directly:

```bash
python bot_phone.py --config ../config.yaml
```

Stop with Ctrl+C (Volume Down + C in Termux), or `Ctrl+C`
on a keyboard.

## 6. Calibrate for your S21+

Your S21+ is 1080 x 2400, and `config.yaml` already uses
that. Still check once:

- Turn on Developer options > "Pointer location"
- Open a match, touch Pass / Shoot / Sprint and note x,y
- Edit `config.yaml` in Termux with `nano config.yaml`

## Troubleshooting

- `adb: device unauthorized` — accept the prompt on the phone,
  or re-pair.
- `adb devices` empty — wireless debugging turned off after
  reboot. Re-pair, it takes 30 seconds.
- Bot taps in the wrong place — your control layout moved.
  Re-calibrate, or switch eFootball to Classic controls.
- Termux killed in background — keep Termux in the foreground,
  or turn off battery optimisation for Termux.
- OpenCV is NOT used here on purpose: the phone version uses
  Pillow + numpy only, because OpenCV is heavy to install
  in Termux.

## Files here

- `bot_phone.py` — phone-only bot (Pillow + numpy, no OpenCV)
- `setup_termux.sh` — installs everything in Termux
- `run.sh` — pairs/connects wireless ADB, then runs the bot
