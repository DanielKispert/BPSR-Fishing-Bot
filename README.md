<p align="left">
    <a href="#"><img alt="Project Version" src="https://img.shields.io/badge/version-1.0.0-blue"></a>
    <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-GPL--3.0-brightgreen"></a>
    <a href="https://www.python.org"><img alt="Python" src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python"></a>
    <a href="https://opencv.org"><img alt="OpenCV" src="https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv"></a>
</p>

# BPSR Fishing Bot

> Forked from [hyuse98/BPSR-Fishing-Bot](https://github.com/hyuse98/BPSR-Fishing-Bot) with these additions:
>
> *   **Tension management** — OCR-based detection of "Tension XX%" overlay; releases mouse at ≥ 90% to prevent fish escapes
> *   **Auto-buy bait/rods** — new BUYING state with full shop flow (WIP)
> *   **Detector improvements** — HSV tuning, windowed scaling, NaN/inf handling, JPG screenshots
> *   **Minigame tuning** — improved arrow handling, idle detection, timing tweaks
> *   **Logging** — rotating file logger and stats via logger
> *   **Updated templates** — no_rod, continue, success, fish_size
> *   **Global hotkeys** — F6–F11 control the bot from any window
> *   **TOML configuration** — persistent user settings via `%LOCALAPPDATA%\BPSR-Fishing-Bot\config.toml`
> *   **Installer** — packaged as a Windows installer (`BPSR-Fishing-Bot-Setup-x.x.x.exe`) for end users

An automated and open-source fishing bot built in Python. It uses image detection to identify on-screen events and interact with a game's fishing minigame, automating the entire process.

---

## Table of Contents

*   [Features](#features)
*   [Quick Start Guide](#quick-start-guide)
    *   [Prerequisites](#1-prerequisites)
    *   [Installation](#2-installation)
    *   [How to Run](#3-how-to-run)
*   [Known Issues and Solutions](#known-issues-and-solutions)
*   [Configuration](#configuration)
*   [For Developers](#for-developers)
    *   [Architecture](#architecture)
    *   [Project Structure](#project-structure)
*   [Future Plans](#future-plans)

---

## Features

*   **Fully Automated Fishing:** Casts the line, detects a bite, and starts the minigame.
*   **Smart Minigame Player:** Autonomously plays the fishing minigame, moving left and right as needed.
*   **Tension Management:** Monitors the "Tension XX%" overlay via OCR; releases mouse at ≥ 90% to prevent fish escapes.
*   **Automatic Rod Swapping:** Detects when the fishing rod breaks and replaces it, allowing for uninterrupted fishing sessions.
*   **Global Hotkey Control:** Start, pause, resume, and stop the bot from any window using F6–F11.
 *   **Persistent Configuration:** User settings stored in `%LOCALAPPDATA%\BPSR-Fishing-Bot\config.toml` — survive updates.
*   **Robust Architecture:** Built with a state machine and solid design principles, making the code easy to understand and extend.

---

## Quick Start Guide

### 1. Prerequisites

*   **Python 3.9+** (for running from source)
*   The game configured to run in full-screen mode at **1920x1080** resolution.

### 2. Installation

#### Option A — Installer (recommended for end users)

 1.  Go to the [**Releases page**](../../releases/latest) and download `BPSR-Fishing-Bot-Setup-x.x.x.exe`.
2.  Run the installer (Next → Install → Finish). No Python required.

#### Option B — From source

1.  Clone this repository:
    ```bash
    git clone https://github.com/DanielKispert/BPSR-Fishing-Bot.git
    cd BPSR-Fishing-Bot
    ```

2.  Install the package in editable mode (includes dev dependencies):
    ```bash
    pip install -e ".[dev]"
    ```

### 3. How to Run

1.  Open the game and make sure it is visible on the screen.
2.  Be at a fishing location. Either stand on an interactable fishing spot or already in the fishing UI.
 3.  If using the installer, launch **BPSR Fishing Bot** from the desktop shortcut. If running from source:
    ```bash
    python main.py
    ```
4.  Press **F6** to start. The bot will cast, detect bites, and play the minigame automatically.
5.  Press **F7** to pause/resume, or **F8** to stop immediately.

#### Hotkeys

| Key | Action |
|-----|--------|
| **F6** | Start (normal mode) |
| **F7** | Pause / Resume |
| **F8** | Emergency stop |
| **F9** | Start in debug mode (saves detection screenshots) |
| **F10** | Toggle burst screenshots (captures every detection frame) |
| **F11** | Toggle ROI visualiser |

---

## Known Issues and Solutions

This section lists common issues you might encounter and how to solve them.

### The detection of an item (e.g., broken rod, fish bite) stops working

*   **Symptom:** The bot stops reacting to a specific event, such as not swapping a broken rod or not detecting a bite.
*   **Likely Cause:** The game may have received a minor visual update, changing the appearance of the icon or image the bot is looking for.
*   **Solution:**
    1.  **Take a new screenshot** of the failed image (e.g., the broken rod icon).
    2.  **Replace the corresponding template file** in `src/fishbot/assets/templates/`.
    3.  If the problem persists, try **lowering the `precision` value** in `config.toml` (e.g., from `0.65` to `0.55`).

### Character won't resume fishing after a timeout state

*   **Symptom:** Something unexpected occurred (like the fish escaping) and the bot has exited the fishing UI and won't restart.
*   **Cause:** When the bot exits the UI it attempts to re-enter by interacting with the fishing spot. Some spots move the player after interaction, so the bot idles trying to interact when nothing is available. The bot does not currently search for the nearest fishing spot.
*   **Solution:** Move your character to an interactable fishing spot to let the bot resume.

### Tension bar / OCR not working

*   **Symptom:** The bot never releases early on high tension; you see OCR-related errors in the log.
*   **Cause:** Tesseract OCR is not installed or not on PATH.
*   **Solution:** Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki). If it was placed in a non-standard location, set `tesseract_path` in `config.toml` (see [Configuration](#configuration)).

---

## Configuration

User settings are stored in `%LOCALAPPDATA%\BPSR-Fishing-Bot\config.toml`. Create this file manually to override defaults. You can find `src/fishbot/config/default_config.toml` as a reference for all available options.

#### `[behavior]`
General bot behaviour.
*   `casting_delay`: Seconds to wait before each cast (default: `0.5`).
*   `target_fps`: Target frames per second for the detection loop (`0` = unlimited).
*   `anti_detection`: Adds randomised delays and mouse jitter to reduce detection risk (default: `true`).

#### `[detection]`
Image matching settings.
*   `precision`: Minimum confidence (from `0.0` to `1.0`) for a template to be considered a match (default: `0.65`).
*   `rois` (Regions of Interest): Rectangles `(x, y, width, height)` that limit the search area for each template, increasing performance and accuracy.

#### `[ocr]`
Tesseract OCR settings used for tension-bar reading.
*   `tesseract_path`: Full path to the Tesseract executable. Set to "auto" for automatic detection (default).

#### `[screen]`
Screen detection settings.
*   `game_window_title`: Title of the game window for auto-detection (default: "Blue Protocol: Star Resonance").
*   `reference_width`, `reference_height`: Reference resolution for ROI scaling (default: 1920×1080).

---

## For Developers

### Architecture

The bot uses a **Finite State Machine (FSM)** to manage its workflow. The logic is divided as follows:

*   **`main.py`**: The entry point that initialises and runs the bot.
*   **`src/fishbot/core/state/`**: Contains the state machine logic.
    *   `state_machine.py`: Manages the current state and transitions.
    *   `impl/`: Houses the classes for each concrete state (`CheckingRodState`, `PlayingMinigameState`, etc.), each implementing a single responsibility.
*   **`src/fishbot/core/game/`**: Modules that interact directly with the game.
    *   `detector.py`: Screen capture and template detection using `mss` and `OpenCV`.
    *   `controller.py`: Simulates keyboard and mouse inputs.
*   **`src/fishbot/config/config_manager.py`**: Loads and validates `config.toml` using Pydantic; provides a typed settings object to the rest of the application.
*   **`src/fishbot/utils/`**: Utility modules, including the rotating file logger.

### Project Structure

```
BPSR-Fishing-Bot/
├── src/
│   └── fishbot/
│       ├── assets/
│       │   └── templates/          # Images (templates) for detection
│       ├── config/                 # Configuration modules
│       │   ├── config_manager.py   # TOML loading + Pydantic validation
│       │   ├── bot_config.py
│       │   ├── detection_config.py
│       │   ├── paths.py
│       │   └── screen_config.py
│       ├── core/
│       │   ├── game/               # Game interaction (Detector, Controller)
│       │   └── state/              # State Machine Logic
│       │       └── impl/           # Individual state classes
│       └── utils/                  # Utility modules (logger)
├── installer/                      # Inno Setup scripts
├── .gitignore
├── build.bat                       # PyInstaller build script
├── bpsr-fishing-bot.spec
├── main.py                         # Application entry point
├── pyproject.toml
└── README.md
```

## Future Plans

*   [ ] Graphical user interface (GUI) for easier configuration.
*   [x] Hotkey system to start/stop the bot.
*   [ ] Configurable hotkeys via `config.toml`.
*   [ ] Improve resilience to unexpected in-game events.
*   [ ] Multi-resolution support (beyond 1920×1080).

---

Feel free to open an *issue* or submit a *pull request*!
