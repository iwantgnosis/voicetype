import tempfile
from pathlib import Path

from faster_whisper import WhisperModel


class WhisperTranscriber:
    def __init__(self):
        self._model = None
        self._model_name = None

    def _ensure_model(self, model_name: str) -> None:
        if self._model is not None and self._model_name == model_name:
            return

        self._model = WhisperModel(model_name, device="cpu", compute_type="int8")
        self._model_name = model_name

    def transcribe_bytes(self, audio_bytes: bytes, model_name: str) -> str:
        if not audio_bytes:
            return ""

        self._ensure_model(model_name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(audio_bytes)

        try:
            segments, _ = self._model.transcribe(str(temp_path), vad_filter=True)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return text
        finally:
            temp_path.unlink(missing_ok=True)
