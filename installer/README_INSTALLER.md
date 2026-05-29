# Building the BPSR Fishing Bot Installer

**Requirements:** Python 3.9+, Inno Setup 6.3+ (https://jrsoftware.org/isdl.php)

## Step 1 -- Build the app

```bat
build.bat
```

Produces `dist\BPSR-Fishing-Bot\`.

## Step 2 -- Compile the installer

Open `installer\bpsr-fishing-bot.iss` in the Inno Setup IDE and press **F9**.

Output: `installer\Output\BPSR-Fishing-Bot-Setup-1.0.0.exe`

**Command line alternative:**
```bat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\bpsr-fishing-bot.iss
```

## Updating the version

Change `#define AppVersion "0.1.3"` in `bpsr-fishing-bot.iss`.
