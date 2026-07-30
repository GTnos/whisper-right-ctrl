from __future__ import annotations

import logging
import queue
import time

import numpy as np


def add_nvidia_dll_directories(project_root) -> None:
    import os
    from pathlib import Path

    for relative in (
        ".venv/Lib/site-packages/nvidia/cublas/bin",
        ".venv/Lib/site-packages/nvidia/cudnn/bin",
    ):
        directory = Path(project_root) / relative
        if directory.is_dir():
            os.environ["PATH"] = str(directory) + os.pathsep + os.environ["PATH"]
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(str(directory))


class SoundDeviceRecorder:
    def __init__(
        self,
        device=None,
        sample_rate: int = 16000,
        fallback_devices=(),
        on_device_changed=None,
        stream_factory=None,
    ) -> None:
        self.device = device
        self.sample_rate = sample_rate
        self.fallback_devices = list(fallback_devices)
        self.on_device_changed = on_device_changed
        self.stream_factory = stream_factory
        self._stream = None
        self._chunks = queue.SimpleQueue()

    def set_devices(self, primary, fallbacks=()) -> None:
        self.device = primary
        self.fallback_devices = list(fallbacks)

    def _callback(self, indata, frames, timing, status) -> None:
        if status:
            logging.warning("Audio status: %s", status)
        self._chunks.put(indata[:, 0].copy())

    def start(self) -> None:
        if self.stream_factory is None:
            import sounddevice as sd

            create_stream = sd.InputStream
        else:
            create_stream = self.stream_factory

        self._chunks = queue.SimpleQueue()
        candidates = list(dict.fromkeys([self.device, *self.fallback_devices]))
        last_error = None
        for candidate in candidates:
            stream = None
            try:
                stream = create_stream(
                    device=candidate,
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="float32",
                    callback=self._callback,
                )
                stream.start()
            except BaseException as error:
                last_error = error
                logging.warning("Unable to open input device %r; trying fallback", candidate, exc_info=True)
                if stream is not None:
                    try:
                        stream.close()
                    except BaseException:
                        pass
                continue
            self._stream = stream
            if candidate != self.device:
                self.device = candidate
                if self.on_device_changed:
                    self.on_device_changed(candidate)
            return
        if last_error is not None:
            raise last_error
        raise RuntimeError("No microphone input device is configured.")

    def stop(self) -> np.ndarray:
        stream, self._stream = self._stream, None
        if stream is None:
            return np.empty(0, dtype=np.float32)
        stream.stop()
        stream.close()
        chunks = []
        while not self._chunks.empty():
            chunks.append(self._chunks.get())
        audio = np.concatenate(chunks) if chunks else np.empty(0, dtype=np.float32)
        if audio.size:
            rms = float(np.sqrt(np.mean(np.square(audio, dtype=np.float64))))
            peak = float(np.max(np.abs(audio)))
            logging.info(
                "Captured %.3fs from device %r; RMS %.6f, peak %.6f",
                audio.size / self.sample_rate,
                self.device,
                rms,
                peak,
            )
        return audio.astype(np.float32, copy=False)


class WhisperTranscriber:
    def __init__(self, config) -> None:
        from faster_whisper import WhisperModel

        self.language = config.language
        self.model = WhisperModel(
            config.model,
            device=config.device,
            compute_type=config.compute_type,
        )

    def warm_up(self) -> None:
        segments, _ = self.model.transcribe(
            np.zeros(16000, dtype=np.float32),
            language=self.language or "zh",
            beam_size=1,
            vad_filter=False,
        )
        list(segments)

    def __call__(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(
            audio,
            language=self.language,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 250},
            condition_on_previous_text=False,
        )
        return " ".join(segment.text.strip() for segment in segments)


class TraditionalChineseConverter:
    def __init__(self) -> None:
        from opencc import OpenCC
        self.converter = OpenCC("s2twp")

    def __call__(self, text: str) -> str:
        return self.converter.convert(text)


class ClipboardInserter:
    def __init__(self, restore: bool = True, restore_delay: float = 0.4) -> None:
        self.restore = restore
        self.restore_delay = restore_delay

    def __call__(self, text: str) -> None:
        import pyperclip
        from pynput.keyboard import Controller, Key

        previous = None
        if self.restore:
            try:
                previous = pyperclip.paste()
            except pyperclip.PyperclipException:
                pass
        pyperclip.copy(text)
        keyboard = Controller()
        with keyboard.pressed(Key.ctrl_l):
            keyboard.press("v")
            keyboard.release("v")
        if previous is not None:
            time.sleep(self.restore_delay)
            pyperclip.copy(previous)
