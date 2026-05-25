<p align="left">
  <a href="#"><img alt="Version" src="https://img.shields.io/badge/version-1.0.0-blue"></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-GPL--3.0-brightgreen"></a>
  <a href="https://www.python.org"><img alt="Python" src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python"></a>
</p>

# 🎣 FishBuddy — Automated Fishing for Blue Protocol: Star Resonance

FishBuddy watches your screen, detects fish bites, and plays the fishing minigame for you — completely hands-free. Cast once, walk away, come back to a full inventory.

> 📸 *Screenshot / GIF coming soon*

**What it does:**
- Casts your line, waits for a bite, and plays the arrow minigame automatically
- Monitors the Tension bar via OCR and releases at the right moment to prevent escapes
- Swaps broken rods automatically so fishing never stops
- Runs quietly in the background — control it with function keys, no window-switching needed

---

## ⬇️ Download & Install

### Step 1 — Download

Go to the [**Releases page**](../../releases/latest) and download the latest `FishBuddy-Setup-x.x.x.exe`.

### Step 2 — Install (5 clicks)

1. Double-click the downloaded installer
2. Click **Next** on the welcome screen
3. Choose an install location (the default is fine)
4. Click **Install**
5. Click **Finish** — a desktop shortcut is created automatically

> ### 🛡️ Windows shows a security warning?
>
> This is normal for unsigned software. Windows SmartScreen may say *"Windows protected your PC"*.
>
> **To run it anyway:**
> 1. Click **More info** (under the warning text)
> 2. Click **Run anyway**
>
> If Windows Defender quarantines the file, see [Troubleshooting](#-troubleshooting) below.

---

## 🚀 Quick Start

1. **Open Blue Protocol: Star Resonance** and go to a fishing spot
2. Make sure the game window is visible (not minimised)
3. **Launch FishBuddy** from your desktop shortcut or Start Menu
4. Press **F6** to start fishing
5. Press **F8** at any time to stop immediately

That's it. FishBuddy takes over from there.

### ⌨️ Hotkeys

| Key | Action |
|-----|--------|
| **F6** | Start / Stop the bot |
| **F7** | Pause / Resume |
| **F8** | Emergency stop — halts all actions immediately |
| **F9** | Toggle debug mode (extra logging) |
| **F10** | Burst screenshot mode — captures every detection frame |
| **F11** | ROI visualiser — shows detection regions on screen |

> Hotkeys work globally — you don't need to click on FishBuddy's window first.  
> All keys can be changed in the config file (see [Settings](#️-settings)).

---

## ⚙️ Settings

FishBuddy is configured through a plain-text file. You don't need to edit it to get started — the defaults work for most players.

### Finding your config file

| Scenario | Config file location |
|----------|---------------------|
| Installed (normal) | `%LOCALAPPDATA%\FishBuddy\config.toml` |
| Portable / next to the .exe | `config.toml` (same folder as `FishBuddy.exe`) |

**To open the config file:**
1. Press `Win + R`, type `%LOCALAPPDATA%\FishBuddy`, press Enter
2. Open `config.toml` with any text editor (Notepad works fine)

> The file is created on first launch. If it doesn't exist yet, run FishBuddy once.

### Key settings

| Setting | Section | Default | What it does |
|---------|---------|---------|-------------|
| `start_stop` | `[hotkeys]` | `"f6"` | Key to start/stop the bot |
| `pause` | `[hotkeys]` | `"f7"` | Key to pause/resume |
| `emergency_stop` | `[hotkeys]` | `"f8"` | Key for immediate stop |
| `anti_detection` | `[behavior]` | `true` | Adds human-like random delays and mouse jitter |
| `casting_delay` | `[behavior]` | `0.5` | Seconds to wait before each cast |
| `debug_mode` | `[behavior]` | `false` | Show extra info in the log window |
| `target_fps` | `[behavior]` | `0` | Detection loop speed (0 = unlimited; try 20 to save CPU) |
| `precision` | `[detection]` | `0.65` | How confident the bot must be to recognise a game element (0.0–1.0) |
| `game_window_title` | `[screen]` | `"Blue Protocol: Star Resonance"` | Window title used to locate the game |
| `tesseract_path` | `[ocr]` | `"auto"` | Path to Tesseract OCR (auto-detected in release builds) |

**Example — change the start/stop key to F2:**
```toml
[hotkeys]
start_stop = "f2"
```

Your config file only needs the settings you want to change — everything else stays at its default automatically.

### Resetting to defaults

Delete (or rename) your `config.toml` file and restart FishBuddy. It will regenerate with all default values.

---

## ❓ Troubleshooting

| Problem | Likely cause | Solution |
|---------|-------------|----------|
| *"Game window not found"* error | Game isn't running or window title differs | Make sure Blue Protocol is open and **not** minimised. If you use a non-English client, set `game_window_title` in config to the exact window title. |
| Bot starts but never casts | Game is running at the wrong resolution | Set the game to **1920×1080** in its Graphics settings. Windowed and borderless modes are both supported. |
| Windows Defender removed the file | Defender flagged the executable | Open **Windows Security → Virus & threat protection → Protection history**, find the item, and click **Restore**. Then add an exclusion for the FishBuddy folder. |
| Bot doesn't detect fish bites | Game had a visual update and templates no longer match | Lower `precision` in config from `0.65` to `0.55`. If it still fails, open an [issue](../../issues) so templates can be updated. |
| Hotkeys don't respond | Another application is capturing the same keys | Change the conflicting hotkeys in your `config.toml` (see Settings above). FishBuddy uses Win32 and does **not** require administrator rights. |
| Bot gets stuck after fish escapes | Character walked away from the fishing spot | Move your character back to an interactable fishing spot — the bot will resume automatically. |
| OCR / Tension bar not working | Tesseract not found | In release builds Tesseract is bundled automatically. If you're running from source, install it from [UB-Mannheim's release page](https://github.com/UB-Mannheim/tesseract/wiki) and set `tesseract_path` in config. |
| High CPU usage | Detection loop running uncapped | Set `target_fps = 20` in the `[behavior]` section of your config. |

---

## 🔧 For Developers

<details>
<summary>Click to expand developer instructions</summary>

### Running from source

**Requirements:** Python 3.9+, Git

```bash
git clone https://github.com/your-username/BPSR-Fishing-Bot.git
cd BPSR-Fishing-Bot
pip install -r requirements.txt
python main.py
```

Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) separately when running from source (not bundled in the repo). Set `tesseract_path` in `config.toml` if auto-detection fails.

### Building the release

```bash
# 1. Install dev dependencies
pip install pyinstaller

# 2. Build the onedir bundle
build.bat        # or: pyinstaller fishbuddy.spec

# 3. Package into installer
# Open fishbuddy_installer.iss in Inno Setup and click Build
```

The output installer is placed in `dist/Output/`.

### Architecture

FishBuddy is built on a **Finite State Machine (FSM)**:

```
STARTING → CHECKING_ROD → CASTING_BAIT → WAITING_FOR_BITE
                ↑                               ↓
           FINISHING ←── PLAYING_MINIGAME ──────┘
```

Key modules:

| Module | Responsibility |
|--------|---------------|
| `main.py` | Entry point; wires up hotkeys and starts the FSM loop |
| `src/fishbot/core/state/` | State machine + individual state classes |
| `src/fishbot/core/game/detector.py` | Screen capture (`mss`) + template matching (`OpenCV`) |
| `src/fishbot/core/game/controller.py` | Keyboard/mouse simulation (`PyAutoGUI`) |
| `src/fishbot/config/config_manager.py` | TOML loading, deep-merge, Pydantic v2 validation |
| `src/fishbot/utils/` | Rotating file logger, stats |

### Project structure

```
BPSR-Fishing-Bot/
├── src/fishbot/
│   ├── assets/templates/   # PNG templates for OpenCV matching
│   ├── config/             # config_manager.py + default_config.toml
│   │   ├── core/
│   │   ├── game/           # Detector, Controller
│   │   └── state/          # FSM + state implementations
│   └── utils/              # Logger
├── main.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

### Contributing

1. Fork the repo and create a feature branch
2. Run existing tests before making changes
3. Keep PRs focused — one feature or fix per PR
4. Open an issue first for large changes so we can discuss the approach

</details>

---

## ⚠️ Disclaimer

- FishBuddy may violate Blue Protocol: Star Resonance's Terms of Service. **Use at your own risk.**
- The authors are not responsible for any account suspension or other consequences.
- This software is provided **as-is**, with no warranty of any kind.
- This project is not affiliated with or endorsed by Bandai Namco or Amazon Games.
