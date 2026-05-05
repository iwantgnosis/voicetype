# Voice Typing Assistant Build Spec

## Project Summary

Build a **Windows desktop voice typing assistant** using **Python** and a **local Whisper model**, not any paid API.

The app should:

- run in the background
- start automatically when Windows starts
- work with a global shortcut key
- record from the microphone
- transcribe speech locally using Whisper
- paste the result directly into the currently active search box, text field, or input area
- also let the user copy the transcript manually if needed

This is meant to be a **small but polished utility app**, not a large dashboard project.

---

## Main Goal

Create a small floating voice assistant UI that feels modern and minimal.

The app should feel like:

- a floating voice bubble or orb
- always visible or easy to bring back
- elegant and compact
- not like a normal large software window

This is a **system-wide voice typing tool**.

---

## Very Important Requirements

### 1. No paid Whisper API

Use a **local Whisper model** only.

Preferred:

- `faster-whisper`

Model options:

- `tiny`
- `base`
- `small`

Default model:

- `base`

---

### 2. Background startup behavior

The app should:

- start automatically when the computer starts
- run silently in the background
- be accessible with a global shortcut key
- optionally show a tray icon

---

### 3. Global shortcut behavior

Example shortcut:

- `Ctrl + Alt + Space`

Behavior:

1. Press shortcut once -> start recording
2. Press shortcut again -> stop recording
3. Transcribe audio locally
4. Insert the text into the current active text field

This must work in places like:

- Google search
- YouTube search
- browser search bars
- Notepad
- Word
- chat input boxes

---

### 4. Two output modes are required

The app must support both:

#### Mode A: Auto Paste

- after transcription, automatically paste text into the active field

#### Mode B: Copy Only

- after transcription, copy the result to clipboard only
- user can manually paste it anywhere

There should be a setting to switch between:

- `Auto Paste`
- `Copy Only`

Optional:

- support both at the same time by copying to clipboard first and then auto-pasting

---

## UI Requirements

## The current kind of UI I do NOT want

Do not make it:

- a large settings window
- a box-heavy dashboard
- a transcript-heavy application
- something that opens big text areas by default
- something that always shows the recognized text in a visible popup

I do **not** want a transcript panel to keep appearing during normal use.

---

## The UI I want

Create a **small floating voice widget**.

It should:

- stay on top
- be compact
- look smooth and modern
- have a listening animation
- have a processing animation
- open settings only when clicked

The default interface should only show:

- small icon / orb
- status text like:
  - `Ready`
  - `Listening`
  - `Processing`

Optional small subtext:

- `Click to speak`
- `Press hotkey`

---

## Floating Widget Design

Design direction:

- minimal
- premium
- soft glow
- rounded
- modern desktop utility feel

Suggested style:

- floating orb or pill
- dark glassmorphism or clean dark theme
- subtle cyan / teal glow while listening
- amber/orange tone while processing
- soft idle animation

The widget should be:

- draggable
- always-on-top
- borderless or nearly borderless
- lightweight

---

## Interaction Design

### Default state

Show:

- orb/icon
- `Ready`

### Listening state

Show:

- animated pulse
- `Listening`

### Processing state

Show:

- different animation
- `Processing`

### Done state

Do not show a large transcript popup automatically.

Instead:

- paste into the form directly if `Auto Paste` is enabled
- copy to clipboard if `Copy Only` is enabled
- optionally show a very small success state such as:
  - `Inserted`
  - `Copied`

---

## Settings Panel

When the floating widget is clicked on a settings icon, open a **small clean settings panel**.

This settings panel can include:

- model selection: `tiny`, `base`, `small`
- hotkey setting
- startup on Windows toggle
- output mode:
  - `Auto Paste`
  - `Copy Only`
- optional `Auto Paste + Copy`

The settings panel should:

- not be large
- not be visually heavy
- match the floating widget style

---

## Transcript Handling

Important:

- do not show the transcript in a big popup during normal use
- do not interrupt the flow
- do not force the user to close transcript windows every time

If transcript viewing is needed, make it optional:

- maybe a small history button
- or a settings option

But by default the app should behave like a utility:

- listen
- transcribe
- insert or copy
- finish

---

## Technical Requirements

Build this in Python for Windows.

Suggested stack:

- `faster-whisper`
- `sounddevice`
- `numpy`
- `keyboard` or `pynput`
- `pyperclip`
- `customtkinter` or `PySide6`
- optional `pystray`

If possible, prefer a GUI approach that allows:

- smoother animation
- floating widget styling
- topmost compact window

If `PySide6` gives better UI quality than `customtkinter`, use `PySide6`.

---

## Architecture Suggestion

Suggested file structure:

```text
voice_typing_assistant/
├─ app.py
├─ gui.py
├─ recorder.py
├─ transcriber.py
├─ hotkeys.py
├─ typer.py
├─ startup.py
├─ settings.py
├─ assets/
└─ requirements.txt
```

---

## Functional Requirements

The finished app should support:

- local Whisper transcription
- startup with Windows
- global hotkey
- floating always-on-top widget
- draggable widget
- listening animation
- processing animation
- settings panel
- auto paste mode
- copy only mode
- stable clipboard handling

---

## UX Requirements

The app should feel:

- fast
- quiet
- useful
- polished
- non-intrusive

The user should not feel like they are opening a full application every time.

It should feel like a small assistant layer over Windows.

---

## What to Avoid

Avoid:

- big transcript windows
- too many buttons on the main widget
- large dashboard-style layouts
- unnecessary debug text
- technical-looking student-project UI
- forced transcript preview after every recording

---

## Best Expected User Flow

1. Computer starts
2. App runs in background
3. User opens any search box or typing field
4. User presses hotkey
5. Widget shows `Listening`
6. User speaks
7. User presses hotkey again
8. Widget shows `Processing`
9. App transcribes locally
10. Text is either:
   - pasted directly
   - copied to clipboard
11. Widget returns to `Ready`

---

## Final Build Request

Build this as a polished Python Windows desktop utility with emphasis on:

- good floating UI
- smooth compact interaction
- no unnecessary transcript popup
- both auto-paste and copy-only workflows
- local Whisper model only

The priority is:

1. better GUI quality
2. correct background behavior
3. proper hotkey workflow
4. reliable text insertion / clipboard behavior

