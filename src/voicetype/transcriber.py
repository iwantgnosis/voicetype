import tempfile
import shutil
import time
import threading
from pathlib import Path
from .logger import get_logger

logger = get_logger("transcriber")

class WhisperTranscriber:
    def __init__(self):
        self._model = None
        self._model_name = None
        self._model_class = None
        self._model_lock = threading.Lock()

    def get_model_dir(self, model_name: str) -> Path:
        """Returns the local directory where the model is stored."""
        home = Path.home()
        return home / ".cache" / "huggingface" / "hub" / f"models--Systran--faster-whisper-{model_name}"

    def is_model_downloaded(self, model_name: str) -> bool:
        """Checks if the model directory exists and has content."""
        path = self.get_model_dir(model_name)
        exists = path.exists() and any(path.iterdir())
        logger.debug(f"Checking model {model_name} at {path}: {'Exists' if exists else 'Missing'}")
        return exists

    def delete_model(self, model_name: str) -> bool:
        """Deletes the model directory."""
        path = self.get_model_dir(model_name)
        if path.exists():
            logger.info(f"Deleting model {model_name} from {path}")
            shutil.rmtree(path)
            if self._model_name == model_name:
                self._model = None
                self._model_name = None
            return True
        return False

    def _ensure_model(self, model_name: str) -> None:
        with self._model_lock:
            if self._model is not None and self._model_name == model_name:
                return

            logger.info(f"Loading Whisper model: {model_name}...")
            start_time = time.time()
            try:
                if self._model_class is None:
                    from faster_whisper import WhisperModel
                    self._model_class = WhisperModel

                self._model = self._model_class(model_name, device="cpu", compute_type="int8")
                self._model_name = model_name
                logger.info(f"Model {model_name} loaded in {time.time() - start_time:.2f}s")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}", exc_info=True)
                raise

    def preload_model(self, model_name: str) -> None:
        logger.info(f"Preloading Whisper model in background: {model_name}")
        self._ensure_model(model_name)

    def transcribe_bytes(self, audio_bytes: bytes, model_name: str) -> str:
        if not audio_bytes:
            logger.warning("No audio bytes provided for transcription.")
            return ""

        logger.info(f"Starting transcription with model: {model_name} (Audio size: {len(audio_bytes)} bytes)")
        self._ensure_model(model_name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(audio_bytes)
            logger.debug(f"Temporary audio file created: {temp_path}")

        try:
            start_time = time.time()
            segments, _ = self._model.transcribe(str(temp_path), vad_filter=True)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            duration = time.time() - start_time
            logger.info(f"Transcription complete in {duration:.2f}s. Result: '{text}'")
            return text
        except Exception as e:
            logger.error(f"Error during transcription: {e}", exc_info=True)
            raise
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
                logger.debug(f"Temporary file deleted: {temp_path}")
