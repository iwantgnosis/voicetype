import time

import keyboard
import pyperclip


def paste_text(text: str) -> None:
    if not text:
        return

    pyperclip.copy(text)
    time.sleep(0.1)
    keyboard.press_and_release("ctrl+v")
