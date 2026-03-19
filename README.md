# hsr-bot (MVP: Launch + Login)

Phase 0.5 MVP for Honkai Star Rail automation.

## Current scope
- Launch HoYoPlay
- Detect launcher/login/game start screens via template matching
- Perform login if needed (env-var credentials)
- Click Start to launch HSR
- Detect in-game landing screen
- Send success/failure report to Telegram bot chat

## Not in this MVP
- Dispatch
- Daily training
- Farming
- Full scheduler/state machine

## Run
```bash
cd /home/clawed/projects/hsr-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --run launch_mvp
```

## Environment variables
- `HSR_USERNAME` (optional; only used if login screen appears)
- `HSR_PASSWORD` (optional; only used if login screen appears)
- `TELEGRAM_BOT_TOKEN` (optional but recommended)
- `TELEGRAM_CHAT_ID` (optional; if omitted no Telegram message is sent)

## Notes
- Designed for Windows runtime.
- Templates currently sourced from: `/mnt/c/Users/Clawed/Pictures/hsr-templates`
- ALT cursor unlock step is included before in-game clicks.
