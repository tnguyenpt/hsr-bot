# HSR Bot (Honkai Star Rail Automation)

Windows automation bot for repeatable daily HSR tasks.

## Product Lens (PM framing)

**Problem:** daily game maintenance tasks are repetitive and easy to miss.

**Who it's for:** players who want reliable daily routine execution with reporting.

**Job to be done:** *"Run my daily routine at a scheduled time and tell me what happened."*

**MVP Success Criteria (current phase):**
- Launch HoYoPlay reliably
- Handle login if prompted
- Launch HSR and confirm game-ready state
- Report success/failure

## Current status

This repo is in **Phase 0.5 MVP** (launch + login reliability).

### Implemented
- Launch HoYoPlay from configured path
- Detect launcher/login/start/game screens via template matching
- AHK-based input actions (click/type/key/hotkey)
- ALT cursor unlock step
- Failure screenshots + logs
- Telegram status reporting

### Planned (next phases)
- Dispatch claim/resend
- Daily training automation
- Stamina farm loop (Build Target)
- Full state machine scheduler

## Architecture

- **Python = brain** (state, vision, decisions)
- **AutoHotkey = hands** (stateless UI input actions)
- **OpenCV template matching** for screen state
- **Telegram reporting** for run outcomes

```text
hsr-bot/
├── main.py
├── missions/launch.py
├── vision/
├── ahk/actions.ahk
├── telegram_bot/reporter.py
└── config/settings.yaml
```

## Run (MVP)

```bash
cd /home/clawed/projects/hsr-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --run launch_mvp
```

### Stage A reliability test (launch/login/ready/close loop)

```bash
python main.py --run stage_a --loops 10
```

This runs 10 repeated cycles and reports pass/fail summary.

## Environment variables

- `HSR_USERNAME` (optional; only if login prompt appears)
- `HSR_PASSWORD` (optional; only if login prompt appears)
- `TELEGRAM_BOT_TOKEN` (optional)
- `TELEGRAM_CHAT_ID` (optional)
- `AHK_EXE` (optional override for AutoHotkey executable path)

## Tradeoffs

- Prioritized robust launch/login over broad feature scope
- Chose template-based detection over hardcoded coordinates
- Deferred full gameplay automation until launch pipeline is stable

## Suggested screenshots (portfolio)

Add these files under `docs/screenshots/`:

- `launcher-detected.png`
- `login-handled.png`
- `game-ready-detected.png`
- `telegram-report-example.png`

When ready, they can be embedded directly in this README.

## Next iteration (portfolio roadmap)

- Expand to mission modules (dispatch/daily/farm)
- Add deterministic dry-run mode
- Harden retry/error-state behavior
- Add nightly run telemetry summary
