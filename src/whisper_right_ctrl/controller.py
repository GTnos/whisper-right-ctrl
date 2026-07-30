from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Protocol

import numpy as np


class Recorder(Protocol):
    def start(self) -> None: ...
    def stop(self) -> np.ndarray: ...


def clean_transcript(text: str) -> str:
    return " ".join(text.split()).strip()


class PushToTalkController:
    def __init__(
        self,
        *,
        recorder: Recorder,
        transcriber: Callable[[np.ndarray], str],
        converter: Callable[[str], str],
        inserter: Callable[[str], None],
        sample_rate: int = 16000,
        minimum_seconds: float = 0.25,
        on_state_change: Callable[[str], None] | None = None,
        on_recording_error: Callable[[BaseException], None] | None = None,
    ) -> None:
        self.recorder = recorder
        self.transcriber = transcriber
        self.converter = converter
        self.inserter = inserter
        self.minimum_samples = round(sample_rate * minimum_seconds)
        self.on_state_change = on_state_change
        self.on_recording_error = on_recording_error
        self._state = "ready"
        self._paused = False
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def paused(self) -> bool:
        with self._lock:
            return self._paused

    def _set_state(self, state: str) -> None:
        with self._lock:
            self._state = state
        if self.on_state_change:
            self.on_state_change(state)

    def set_paused(self, paused: bool) -> None:
        with self._lock:
            if self._state == "recording":
                return
            self._paused = paused
        self._set_state("paused" if paused else "ready")

    def press(self) -> bool:
        with self._lock:
            if self._paused or self._state != "ready":
                return False
            self._state = "recording"
        try:
            self.recorder.start()
        except BaseException as error:
            logging.exception("Unable to start recording")
            self._set_state("ready")
            if self.on_recording_error:
                self.on_recording_error(error)
            return False
        if self.on_state_change:
            self.on_state_change("recording")
        return True

    def release(self) -> bool:
        with self._lock:
            if self._state != "recording":
                return False
            self._state = "transcribing"
        if self.on_state_change:
            self.on_state_change("transcribing")
        try:
            audio = self.recorder.stop()
        except BaseException:
            logging.exception("Unable to stop recording")
            self._set_state("ready")
            return False
        threading.Thread(
            target=self._process_audio,
            args=(audio,),
            name="whisper-transcription",
            daemon=True,
        ).start()
        return True

    def _process_audio(self, audio: np.ndarray) -> None:
        try:
            if audio.size < self.minimum_samples:
                return
            text = clean_transcript(self.transcriber(audio))
            if text:
                text = clean_transcript(self.converter(text))
            if text:
                self.inserter(text)
        except BaseException:
            logging.exception("Voice transcription failed")
        finally:
            self._set_state("paused" if self.paused else "ready")
