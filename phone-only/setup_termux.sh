#!/data/data/com.termux/files/usr/bin/bash
# Setup for Termux on Samsung Galaxy S21+ (phone-only, no PC)
set -e
pkg update -y
pkg install -y python android-tools
pip install --upgrade pip
pip install pillow numpy pyyaml
mkdir -p ~/efootball-bot
cp bot_phone.py ~/efootball-bot/
cp ../config.yaml ~/efootball-bot/
cp run.sh ~/efootball-bot/ 2>/dev/null || true
echo ""
echo "Done. Next:"
echo "  cd ~/efootball-bot"
echo "  bash run.sh"
