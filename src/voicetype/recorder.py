import io
import threading
import wave

import numpy as np
import sounddevice as sd
from .logger import get_logger

logger = get_logger("recorder")

class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._chunks = []
        self._recording = False
        self._stream = None
        self._lock = threading.Lock()
        logger.debug(f"AudioRecorder initialized: {sample_rate}Hz, {channels} channels")

    @property
    def is_recording(self) -> bool:
        return self._recording

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.warning(f"Audio stream status: {status}")
            return
        with self._lock:
            self._chunks.append(indata.copy())

    def start(self) -> None:
        if self._recording:
            logger.warning("Attempted to start recording while already recording.")
            return
        
        logger.info("Starting audio recording...")
        self._chunks = []
        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                callback=self._audio_callback,
            )
            self._stream.start()
            self._recording = True
            logger.debug("Audio stream started successfully.")
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}", exc_info=True)
            raise

    def stop(self) -> bytes:
        if not self._recording:
            logger.warning("Attempted to stop recording while not recording.")
            return b""

        logger.info("Stopping audio recording...")
        self._recording = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
                self._stream = None
                logger.debug("Audio stream stopped and closed.")
            except Exception as e:
                logger.error(f"Error while closing audio stream: {e}", exc_info=True)

        with self._lock:
            if not self._chunks:
                logger.warning("Recording stopped, but no audio chunks were collected.")
                return b""
            audio = np.concatenate(self._chunks, axis=0)
            logger.debug(f"Concatenated {len(self._chunks)} chunks. Total samples: {len(audio)}")

        audio = np.clip(audio, -1.0, 1.0)
        pcm = (audio * 32767).astype(np.int16)

        buffer = io.BytesIO()
        try:
            with wave.open(buffer, "wb") as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(pcm.tobytes())
            
            audio_data = buffer.getvalue()
            logger.info(f"Audio recording finalized. Size: {len(audio_data)} bytes")
            return audio_data
        except Exception as e:
            logger.error(f"Error while generating WAV data: {e}", exc_info=True)
            return b""
