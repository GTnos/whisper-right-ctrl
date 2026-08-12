from __future__ import annotations

import logging
import threading
from collections.abc import Callable


class ResumeMonitor:
    def __init__(
        self,
        request_recovery: Callable[[], object],
        expected_interval: float = 15.0,
    ) -> None:
        self.request_recovery = request_recovery
        self.expected_interval = expected_interval
        self._last_tick: float | None = None

    def tick(self, now: float) -> None:
        previous, self._last_tick = self._last_tick, now
        if previous is not None and now - previous > self.expected_interval * 3:
            self.request_recovery()


class RecoveryHotkey:
    CONTROL_KEYS = {"ctrl", "ctrl_l"}
    ALT_KEYS = {"alt", "alt_l", "alt_r", "alt_gr"}

    def __init__(self, request_recovery: Callable[[], object]) -> None:
        self.request_recovery = request_recovery
        self._pressed: set[str] = set()

    def press(self, key: str) -> None:
        if key in self._pressed:
            return
        self._pressed.add(key)
        if (
            key == "f12"
            and self._pressed.intersection(self.CONTROL_KEYS)
            and self._pressed.intersection(self.ALT_KEYS)
        ):
            self.request_recovery()

    def release(self, key: str) -> None:
        self._pressed.discard(key)


class RecoveryCoordinator:
    def __init__(
        self,
        recover: Callable[[], None],
        on_state_change: Callable[[str], None] | None = None,
    ) -> None:
        self.recover = recover
        self.on_state_change = on_state_change
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    def request(self) -> bool:
        with self._lock:
            if self._running:
                return False
            self._running = True
        self._thread = threading.Thread(
            target=self._run,
            name="microphone-recovery",
            daemon=True,
        )
        self._thread.start()
        return True

    def _set_state(self, state: str) -> None:
        if self.on_state_change:
            self.on_state_change(state)

    def _run(self) -> None:
        self._set_state("reconnecting")
        try:
            self.recover()
        except BaseException:
            logging.exception("Microphone recovery failed")
            self._set_state("unavailable")
        else:
            self._set_state("ready")
        finally:
            with self._lock:
                self._running = False

    def wait(self, timeout: float | None = None) -> bool:
        thread = self._thread
        if thread is not None:
            thread.join(timeout)
            return not thread.is_alive()
        return True
