# Voice Typing Assistant – Showcase Website Plan

## Overview

A clean, single-page landing site to showcase the Voice Typing Assistant project.
Built with **Python (Flask or FastAPI)** serving static HTML, or pure static HTML hosted on GitHub Pages.

---

## Site Structure

### Hero Section
- **Headline:** "Voice Typing, Reimagined."
- **Subtext:** "A tiny floating assistant that transcribes your speech locally — no cloud, no API keys, no subscription."
- **Visual:** Animated mockup of the pill widget showing idle → listening → inserted states
- **CTA buttons:** `Download for Windows` | `View on GitHub`

### How It Works (3 Steps)
| Step | Icon | Text |
|------|------|------|
| 1 | 🎙️ | **Press the hotkey** — `Ctrl+Alt+Space` activates the mic |
| 2 | 🧠 | **Speak naturally** — Whisper AI transcribes locally on your machine |
| 3 | ✨ | **Text appears instantly** — pasted right into any search bar, editor, or chat |

### Key Features Grid
- 🔒 **100% Offline** — Runs Whisper locally. Your voice never leaves your PC.
- ⚡ **Instant Paste** — Text appears in the active field automatically.
- 🪶 **Ultra Compact** — A tiny curved pill. Never blocks your workflow.
- ⌨️ **Global Hotkey** — Works in any app: Chrome, Notepad, Word, Slack.
- 🎨 **Premium Design** — Dynamic Island-style floating widget with glow animations.
- ⚙️ **Customizable** — Choose model size, hotkey, paste mode from right-click settings.

### Demo Video / GIF
- Screen recording showing:
  1. User opens Google search
  2. Presses hotkey → pill glows teal
  3. Speaks "best restaurants in tokyo"
  4. Pill turns amber briefly
  5. Text appears in the search box
  6. Pill returns to idle
- Looping 8-second GIF, auto-playing, muted

### Tech Stack Section
| Component | Technology |
|-----------|-----------|
| GUI | PySide6 (Qt6) — frameless transparent widget |
| Speech-to-Text | faster-whisper (local Whisper) |
| Audio | sounddevice + numpy |
| Hotkey | keyboard (global system hook) |
| Clipboard | pyperclip |
| System Tray | pystray + Pillow |

### Installation / Quick Start
```bash
git clone https://github.com/yourname/voice-typing-assistant.git
cd voice-typing-assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### FAQ Section
- **Does it need internet?** No. Everything runs locally.
- **Which Whisper models are supported?** tiny, base, small — selectable in settings.
- **Does it work in any app?** Yes, any text field that supports Ctrl+V paste.
- **Is my voice data stored?** No. Audio is processed in-memory and discarded.

### Footer
- GitHub link | License (MIT) | "Made with 🐍 Python"

---

## Design Direction

- **Dark theme** matching the app (background: `#0d1117`)
- **Teal accent** (`#20d5c3`) for CTAs and highlights
- **Font:** Inter or Segoe UI
- **Style:** Minimal, developer-focused, no clutter
- **Animations:** Subtle fade-ins on scroll, floating pill mockup
- **Responsive:** Works on mobile for viewing (app is Windows-only)

---

## Tech Options for Building the Site

| Option | Pros | Cons |
|--------|------|------|
| **Static HTML + CSS + JS** | Simplest, host on GitHub Pages for free | Manual updates |
| **Flask** | Python-native, easy templating | Needs a server |
| **FastAPI + Jinja2** | Modern Python, fast | Overkill for a landing page |
| **GitHub Pages (recommended)** | Free hosting, auto-deploy from repo | Static only |

### Recommendation
**Static HTML/CSS/JS** deployed to **GitHub Pages**. Keep it simple — one `index.html`, one `style.css`, and a few assets. No build step needed.

---

## Files to Create
```
website/
├── index.html          # Single-page landing
├── style.css           # Dark theme styles
├── script.js           # Scroll animations, demo interaction
├── assets/
│   ├── demo.gif        # Screen recording of the app in action
│   ├── pill-mockup.png # Static image of the pill widget
│   └── og-image.png    # Social media preview image
└── README.md           # Deployment instructions
```
