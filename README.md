# VoiceType

Offline voice typing for Windows with local Whisper transcription, a floating pill UI, global hotkeys, and direct paste into the active app.

## What It Does

- Runs fully offline with `faster-whisper`
- Stays available in the background after launch
- Records from a global hotkey or the floating widget
- Pastes the transcript into the active field or copies it to the clipboard
- Shows an `I am ready` startup notification
- Warms up the selected Whisper model in the background after startup

## Current Desktop Behavior

1. Launch the app once.
2. The widget starts quickly and confirms startup with `I am ready`.
3. The selected model begins loading in the background.
4. Press `Ctrl+Alt+Space` to start recording.
5. Press it again to stop and transcribe.
6. The transcript is pasted automatically or copied, depending on settings.

## Tech Stack

- `Python 3.10+`
- `PySide6` for the desktop UI
- `faster-whisper` for local transcription
- `sounddevice` for microphone capture
- `numpy` for audio buffers
- `keyboard` for global hotkeys
- `pyperclip` for clipboard support
- Windows startup integration through the registry

## Project Structure

```text
voice_typing_assistant/
|-- README.md
|-- requirements.txt
|-- run.py
|-- Voicetype.spec
|-- assets/
|-- docs/
|-- flask_showcase/
`-- src/voicetype/
    |-- gui.py
    |-- hotkeys.py
    |-- logger.py
    |-- recorder.py
    |-- settings.py
    |-- startup.py
    |-- transcriber.py
    `-- typer.py
```

## Installation

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

## Build The Windows App

```powershell
pyinstaller --noconfirm Voicetype.spec
```

Use the generated executable here:

```text
dist\Voicetype\Voicetype.exe
```

Do not move only the `.exe` out of that folder. The `_internal` directory beside it is required for the optimized build.

## Static Website

The repo includes a static showcase site in `docs/` for GitHub Pages and a Flask showcase in `flask_showcase/`.

## Limitations

- Windows-focused
- First launch after opening the app still needs to load the model once per app session
- First-time model download depends on internet access
- Global hotkeys can be blocked by some environments or permissions
