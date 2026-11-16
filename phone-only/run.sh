#!/data/data/com.termux/files/usr/bin/bash
# Pair + connect wireless ADB, then run the phone-only bot.
# Run this in Termux after turning on Wireless debugging.
set -e
cd ~/efootball-bot 2>/dev/null || cd "$(dirname "$0")"

if ! adb devices | grep -q "device$"; then
  echo "Wireless debugging: Settings > Developer options > Wireless debugging > ON"
  echo ""
  read -p "Pair IP:port (e.g. 192.168.1.5:45671): " PAIR_ADDR
  read -p "Pairing code (6 digits): " PAIR_CODE
  adb pair "$PAIR_ADDR" "$PAIR_CODE"
  read -p "Connect IP:port from the Wireless debugging screen (e.g. 192.168.1.5:37123): " CONN_ADDR
  adb connect "$CONN_ADDR"
fi

adb devices
echo "Starting bot — open eFootball, offline match vs AI, then come back here."
echo "Stop with Ctrl+C (Volume Down + C)."
python bot_phone.py --config config.yaml
