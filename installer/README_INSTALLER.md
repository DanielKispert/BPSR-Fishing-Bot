# Building the FishBuddy Installer

This directory contains the Inno Setup script that produces a single-file
Windows installer: **`FishBuddy-Setup-1.0.0.exe`**.

---

## Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10+ | https://python.org |
| Inno Setup | 6.3+ | https://jrsoftware.org/isdl.php |
| PyInstaller | installed via `build.bat` | — |

---

## Step 1 — Build the Python application

From the **repo root**, run:

```bat
build.bat
```

This will:
1. Install all Python dependencies from `requirements.txt`
2. Install PyInstaller
3. Run `pyinstaller fishbuddy.spec`
4. Produce `dist\FishBuddy\` — the folder Inno Setup packages up

> **Run `build.bat` every time you change Python source files before
> rebuilding the installer.**

---

## Step 2 — Compile the installer

### Option A — Inno Setup IDE (recommended for first-time users)

1. Install Inno Setup 6 from the link above
2. Open `installer\fishbuddy.iss` in the Inno Setup Compiler
3. Press **F9** (or Build → Compile)
4. The finished installer appears at `installer\Output\FishBuddy-Setup-1.0.0.exe`

### Option B — Command line (CI/CD friendly)

```bat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\fishbuddy.iss
```

---

## Updating the version number

Open `installer\fishbuddy.iss` and change **one line**:

```pascal
#define AppVersion "1.0.0"
```

The output filename, installer title, and registry entries all derive from
this single define.

---

## Bundling Tesseract OCR (optional)

By default FishBuddy relies on a Tesseract installation already present on
the user's machine. To bundle Tesseract inside the installer:

1. Download the Windows portable build from
   https://github.com/UB-Mannheim/tesseract/wiki
2. Extract into `vendor\tesseract\` so that `vendor\tesseract\tesseract.exe`
   exists
3. Copy language data: `vendor\tesseract\tessdata\eng.traineddata`
4. In `fishbuddy.spec` uncomment the two Tesseract sections in `added_datas`
   and `added_binaries`
5. Re-run `build.bat` then recompile the Inno Setup script

Tesseract's own files will be included in `dist\FishBuddy\` and Inno Setup
will pick them up automatically via the `recursesubdirs` flag.

---

## Adding an icon

1. Create or export a `fishbuddy.ico` file (256×256 recommended)
2. Place it at `installer\fishbuddy.ico`
3. In `fishbuddy.spec` uncomment the `icon=` line
4. In `fishbuddy.iss` uncomment the `SetupIconFile=` and
   `UninstallDisplayIcon=` lines
5. Rebuild both (build.bat → Inno Setup)

---

## Adding a license

1. Convert your `LICENSE` file to RTF format (Word, LibreOffice, or an
   online converter work fine)
2. Save as `LICENSE.rtf` in the repo root
3. In `fishbuddy.iss` uncomment the `LicenseFile=` line
4. Recompile the installer — a license acceptance screen will appear

---

## Installer design decisions

| Decision | Reason |
|----------|--------|
| `PrivilegesRequired=lowest` | No UAC prompt; any user can install without admin rights |
| `{autopf}` default dir | Resolves to Program Files for admins, `%LOCALAPPDATA%\Programs` for standard users |
| onedir PyInstaller build | Avoids self-extracting AV heuristics; faster launch than onefile |
| User-data delete prompt | Respects user choice; config at `%LOCALAPPDATA%\FishBuddy\` |
| `lzma2/ultra64` compression | Best compression ratio; acceptable compile time |
