# Offline Voice Typing Assistant

## Project Summary

This project is a small Windows desktop utility built with Python. It runs locally, shows a floating always-on-top voice widget, listens for a global shortcut key, records audio from the microphone, transcribes it using a local Whisper model, and pastes the text into the active app.

This is a good faculty showcase project because it demonstrates:

- AI model usage without paid API calls
- desktop GUI development
- keyboard automation
- audio recording
- practical real-world utility

---

## Main Idea

The app behaves like a lightweight voice typing tool:

1. You start the app once.
2. It stays available in the background.
3. You press a shortcut like `Ctrl+Alt+Space` or click the floating orb.
4. The app starts recording.
5. You press the same shortcut again.
6. The app transcribes your speech using a local Whisper model.
7. The text is pasted into the current typing area.

---

## Why This Matches Market Demand

This project fits current demand because companies want:

- AI-powered tools
- automation utilities
- offline privacy-friendly apps
- productivity software

It is much smaller than a full SaaS product, but still looks modern and practical.

---

## Features

- Offline transcription using a local Whisper model
- Floating always-on-top voice orb
- Animated listening and processing states
- Global hotkey to start and stop recording
- Paste transcript into the active window
- Copy transcript to clipboard
- Save transcript as a text file
- Click-to-open settings panel
- Optional "Start with Windows" support
- Model selection for `tiny`, `base`, and `small`

---

## Recommended Scope for Faculty Demo

Keep the first version focused:

- one hotkey
- one language mode
- one microphone
- one output area
- one-click startup toggle

That is enough to make it useful and easy to explain.

---

## Tech Stack

- `Python 3.10+`
- `customtkinter` for GUI
- `faster-whisper` for local transcription
- `sounddevice` for microphone recording
- `numpy` for audio buffers
- `keyboard` for global hotkeys
- `pyperclip` for clipboard support
- `pystray` and `Pillow` for system tray support

---

## Project Structure

```text
voice_typing_assistant/
├─ README.md
├─ requirements.txt
├─ run.py
├─ app.py
├─ gui.py
├─ hotkeys.py
├─ recorder.py
├─ settings.py
├─ startup.py
├─ transcriber.py
├─ typer.py
└─ flask_showcase/
    ├─ app.py
    ├─ static/
    └─ templates/
```

### Flask Showcase Website

The project also includes a Flask-based showcase website (located in `flask_showcase/`) that provides a high-fidelity interactive preview of the "Dynamic Island" style voice widget, demonstrating the premium UI/UX design and animations.

---

## How the System Works

### 1. GUI Layer

The GUI lets the user:

- choose a Whisper model
- set a hotkey
- enable or disable Windows startup
- see recording and processing status
- preview the transcript

### 2. Hotkey Layer

The hotkey module listens globally for a configured shortcut. The shortcut toggles recording on and off.

### 3. Recording Layer

The recorder captures microphone audio into memory and converts it into a WAV byte stream.

### 4. Transcription Layer

The transcriber loads the selected Whisper model locally using `faster-whisper` and returns the recognized text.

### 5. Typing Layer

The final text is copied to the clipboard and pasted into the active window using `Ctrl+V`.

### 6. Startup Layer

The startup module registers the app in the current user's Windows `Run` registry entry so it can start automatically after login.

---

## Installation Steps

## 1. Install Python

Install Python `3.10` or newer.

Check it:

```powershell
python --version
```

---

## 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

## 3. Install libraries

```powershell
pip install -r requirements.txt
```

---

## 4. Run the app

```powershell
python app.py
```

---

## Exact Libraries Used

These are the packages required by the current code:

- `customtkinter`
- `faster-whisper`
- `sounddevice`
- `numpy`
- `keyboard`
- `pyperclip`
- `pystray`
- `Pillow`

---

## Whisper Model Notes

You said you do not want the Whisper API. This project uses a local model.

Recommended options:

- `tiny`: fastest, lowest accuracy
- `base`: best starting point
- `small`: better accuracy, heavier model

For faculty demo:

- use `base` if your laptop is average
- use `small` if your laptop is strong enough

The model is downloaded automatically by `faster-whisper` the first time you use it.

---

## How to Use It

1. Launch the app.
2. Choose the model.
3. Set the hotkey.
4. Press `Register Hotkey`.
5. Focus any search box or text field.
6. Press the hotkey to start recording.
7. Press it again to stop.
8. Wait for transcription.
9. The text will be pasted automatically.

---

## Example Demo Flow

You can show it in:

- Google search
- YouTube search
- Notepad
- Word
- Chat input boxes

Example:

1. Open Notepad.
2. Put the cursor in the text area.
3. Press the hotkey.
4. Say: `This is my offline Whisper voice typing project`.
5. Press the hotkey again.
6. The text appears in Notepad automatically.

---

## Future Improvements

- language dropdown
- microphone selection
- noise threshold
- history of transcripts
- export to PDF or DOCX
- executable packaging with `pyinstaller`
- settings page with theme options

---

## Faculty Presentation Points

If your faculty asks why this project is useful, say:

- it uses offline AI, so there is no API cost
- it solves a real productivity problem
- it works system-wide with a shortcut key
- it combines GUI, AI, audio, and automation

---

## Limitations

- Works best on Windows
- Global hotkeys may require accessibility permissions in some environments
- Automatic paste depends on the target app accepting normal keyboard paste input
- First model load can take time because the model must download

---

## Best Short Title

`Offline Voice Typing Assistant Using Whisper and Python`
