import keyboard


class HotkeyManager:
    def __init__(self):
        self._registered_hotkey = None

    def register(self, hotkey: str, callback) -> None:
        self.unregister()
        self._registered_hotkey = keyboard.add_hotkey(hotkey, callback, suppress=False)

    def unregister(self) -> None:
        if self._registered_hotkey is not None:
            keyboard.remove_hotkey(self._registered_hotkey)
            self._registered_hotkey = None
