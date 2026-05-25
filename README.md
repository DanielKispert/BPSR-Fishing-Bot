<p align="left">
  <a href="#"><img alt="Version" src="https://img.shields.io/badge/version-1.0.0-blue"></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-GPL--3.0-brightgreen"></a>
  <a href="https://www.python.org"><img alt="Python" src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python"></a>
</p>

# 🎣 FishBuddy — Automated Fishing for Blue Protocol: Star Resonance

Watches your screen, detects bites, and plays the fishing minigame automatically — cast once, walk away.

---

## ⬇️ Download & Install

1. Go to the [**Releases page**](../../releases/latest) and download `FishBuddy-Setup-x.x.x.exe`
2. Run the installer (Next → Install → Finish)

> If Windows SmartScreen warns *"Windows protected your PC"*: click **More info** → **Run anyway**.

---

## 🚀 Quick Start

1. Open Blue Protocol: Star Resonance and go to a fishing spot
2. Launch FishBuddy from your desktop shortcut
3. Press **F6** to start — FishBuddy takes over from there
4. Press **F8** to stop immediately at any time

### ⌨️ Hotkeys

| Key | Action |
|-----|--------|
| **F6** | Start / Stop |
| **F7** | Pause / Resume |
| **F8** | Emergency stop |
| **F9** | Start in debug mode (screenshots) |
| **F10** | Toggle burst screenshots |
| **F11** | Toggle ROI visualiser |

Hotkeys work globally.

---

## ⚙️ Settings

Config file: `%LOCALAPPDATA%\FishBuddy\config.toml` (created on first launch).

| Setting | Section | Default | What it does |
|---------|---------|---------|-------------|
| `anti_detection` | `[behavior]` | `true` | Random delays and mouse jitter |
| `casting_delay` | `[behavior]` | `0.5` | Seconds to wait before each cast |
| `target_fps` | `[behavior]` | `0` | Detection loop speed (0 = unlimited) |
| `precision` | `[detection]` | `0.65` | Match confidence threshold (0.0–1.0) |
| `tesseract_path` | `[ocr]` | `"auto"` | Tesseract path ("auto" = bundled in release) |
| `anti_detection` | `[behavior]` | `true` | Random delays and mouse jitter |
| `casting_delay` | `[behavior]` | `0.5` | Seconds to wait before each cast |
| `target_fps` | `[behavior]` | `0` | Detection loop speed (0 = unlimited) |
| `precision` | `[detection]` | `0.65` | Match confidence threshold (0.0–1.0) |
| `tesseract_path` | `[ocr]` | `"auto"` | Tesseract path ("auto" = bundled in release) |

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| *"Game window not found"* | Make sure the game is open and not minimised |
| Bot never casts | Set game to **1920×1080** in its Graphics settings |
| Windows Defender removed the file | Restore from Protection History, add folder exclusion |
| Bot misses bites | Lower `precision` from `0.65` to `0.55` |
| Hotkeys don't respond | Hotkey customization planned for a future release |
| High CPU usage | Set `target_fps = 20` in `[behavior]` |
| OCR / tension bar not working | Install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and set `tesseract_path` |

---

## 🔧 For Developers

<details>
<summary>Click to expand</summary>

### Running from source

**Requirements:** Python 3.9+, Git

```bash
git clone https://github.com/your-username/BPSR-Fishing-Bot.git
cd BPSR-Fishing-Bot
pip install -e ".[dev]"
python main.py
```

Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) separately when running from source.

### Building the release

```bash
build.bat    # installs deps + runs PyInstaller -> dist\FishBuddy\
# Then open fishbuddy.iss in Inno Setup and press F9
```

### Architecture

FSM: `STARTING → CHECKING_ROD → CASTING_BAIT → WAITING_FOR_BITE → PLAYING_MINIGAME → FINISHING`

| Module | Responsibility |
|--------|---------------|
| `main.py` | Entry point |
| `src/fishbot/core/state/` | FSM states |
| `src/fishbot/core/game/detector.py` | Screen capture + template matching |
| `src/fishbot/config/config_manager.py` | TOML loading + Pydantic validation |

</details>

---

## ⚠️ Disclaimer

FishBuddy may violate Blue Protocol: Star Resonance's Terms of Service. **Use at your own risk.**
Not affiliated with or endorsed by Bandai Namco or Amazon Games.
