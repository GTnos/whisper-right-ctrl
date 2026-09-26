from __future__ import annotations

import ctypes
import logging
import sys
import threading
import time
import winsound
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from PIL import Image, ImageDraw
from pynput import keyboard
import pystray

from whisper_right_ctrl.adapters import (
    ClipboardInserter,
    SoundDeviceRecorder,
    TraditionalChineseConverter,
    WhisperTranscriber,
    add_nvidia_dll_directories,
)
from whisper_right_ctrl.config import MODEL_OPTIONS, app_data_dir, load_config, log_path, save_config
from whisper_right_ctrl.controller import PushToTalkController
from whisper_right_ctrl.microphones import (
    MicrophoneDevice,
    deduplicate_input_devices,
    filter_working_input_devices,
    list_input_devices,
    resolve_input_device,
)
from whisper_right_ctrl.recovery import RecoveryCoordinator, RecoveryHotkey, ResumeMonitor


MUTEX_NAME = "Local\\WhisperRightCtrlVoiceInput"


def configure_logging() -> None:
    app_data_dir().mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_path(),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(threadName)s %(message)s",
        encoding="utf-8",
    )


def acquire_single_instance():
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle or kernel32.GetLastError() == 183:
        return None
    return handle


def make_icon(color="#16A34A"):
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((11, 4, 53, 45), radius=20, fill=color)
    draw.rectangle((27, 40, 37, 54), fill=color)
    draw.rounded_rectangle((17, 50, 47, 58), radius=4, fill=color)
    draw.arc((5, 20, 59, 58), 0, 180, fill="#FFFFFF", width=5)
    return image


class Application:
    def __init__(self):
        self.icon = None
        self.listener = None
        self.requested_exit_code = 0
        self.current_state = "checking"
        self.monitor_stop = threading.Event()
        self.config = load_config()
        detected = list_input_devices()
        detected.sort(key=lambda device: device.index != self.config.input_device)
        logging.info("Checking %s microphone input interfaces", len(detected))
        self.available_microphones = filter_working_input_devices(detected)
        selected = resolve_input_device(
            self.available_microphones,
            self.config.input_device,
            self.config.input_device_name,
        )
        if selected is None:
            raise RuntimeError("Run CONFIGURE_MICROPHONE.cmd before starting.")
        self.microphones = deduplicate_input_devices(
            self.available_microphones,
            preferred_index=selected.index,
        )
        logging.info(
            "Showing %s working microphones from %s usable interfaces",
            len(self.microphones),
            len(self.available_microphones),
        )
        self.config.input_device = selected.index
        self.config.input_device_name = selected.name
        save_config(self.config)
        add_nvidia_dll_directories(PROJECT_ROOT)
        logging.info("Loading %s on %s/%s", self.config.model, self.config.device, self.config.compute_type)
        transcriber = WhisperTranscriber(self.config)
        transcriber.warm_up()
        fallback_devices = [
            device.index
            for device in self.available_microphones
            if device.name == selected.name and device.index != selected.index
        ]
        recorder = SoundDeviceRecorder(
                self.config.input_device,
                fallback_devices=fallback_devices,
                on_device_changed=self.on_recorder_device_changed,
            )
        self.controller = PushToTalkController(
            recorder=recorder,
            transcriber=transcriber,
            converter=TraditionalChineseConverter(),
            inserter=ClipboardInserter(self.config.restore_clipboard),
            minimum_seconds=self.config.minimum_seconds,
            on_state_change=self.on_state_change,
            on_recording_error=self.on_recording_error,
        )
        self.recovery = RecoveryCoordinator(recorder.recover, self.on_recovery_state_change)
        self.recovery_hotkey = RecoveryHotkey(self.request_recovery)
        self.resume_monitor = ResumeMonitor(self.request_recovery)

    def on_state_change(self, state):
        logging.info("State: %s", state)
        self.current_state = state
        colors = {
            "ready": "#16A34A",
            "recording": "#DC2626",
            "transcribing": "#D97706",
            "paused": "#6B7280",
            "checking": "#2563EB",
            "reconnecting": "#2563EB",
            "unavailable": "#7F1D1D",
        }
        if state == "recording":
            winsound.Beep(880, 45)
        elif state == "transcribing":
            winsound.Beep(660, 45)
        if self.icon:
            self.icon.icon = make_icon(colors.get(state, "#6B7280"))
            self.icon.title = f"Whisper Right Ctrl — {state}"
            self.icon.update_menu()

    def on_press(self, key):
        key_name = getattr(key, "name", str(key))
        self.recovery_hotkey.press(key_name)
        if key == keyboard.Key.ctrl_r and not self.recovery.running:
            self.controller.press()

    def on_release(self, key):
        self.recovery_hotkey.release(getattr(key, "name", str(key)))
        if key == keyboard.Key.ctrl_r:
            self.controller.release()

    def toggle_pause(self, icon, item):
        self.controller.set_paused(not self.controller.paused)

    def pause_label(self, item):
        return "Resume Right Ctrl" if self.controller.paused else "Pause Right Ctrl"

    def microphone_checked(self, device: MicrophoneDevice):
        return lambda item: self.controller.recorder.device == device.index

    def microphone_action(self, device: MicrophoneDevice):
        def select(icon, item):
            if self.controller.state not in {"ready", "paused"}:
                icon.notify("Wait until transcription finishes before changing microphone.", "Whisper Right Ctrl")
                return
            fallback_devices = [
                candidate.index
                for candidate in self.available_microphones
                if candidate.name == device.name and candidate.index != device.index
            ]
            self.controller.recorder.set_devices(device.index, fallback_devices)
            self.config.input_device = device.index
            self.config.input_device_name = device.name
            save_config(self.config)
            logging.info("Selected input device: [%s] %s", device.index, device.name)
            icon.notify(f"Microphone: {device.name}", "Whisper Right Ctrl")
            icon.update_menu()

        return select

    def model_checked(self, model: str):
        return lambda item: self.config.model == model

    def model_action(self, model: str):
        def select(icon, item):
            self.config.model = model
            save_config(self.config)
            label = next(label for candidate, label in MODEL_OPTIONS if candidate == model)
            message = f"{label} will be used after restarting Whisper Right Ctrl."
            if model == "large-v3":
                message += " The first launch downloads several GB of model data."
            logging.info("Selected model for next launch: %s", model)
            icon.notify(message, "Whisper Right Ctrl")
            icon.update_menu()

        return select

    def on_recorder_device_changed(self, index):
        device = next(
            (candidate for candidate in self.available_microphones if candidate.index == index),
            None,
        )
        if device is None:
            return
        self.config.input_device = device.index
        self.config.input_device_name = device.name
        save_config(self.config)
        logging.info("Automatically switched input device: [%s] %s", device.index, device.name)
        if self.icon:
            self.icon.notify(f"Recovered microphone: {device.name}", "Whisper Right Ctrl")
            self.icon.update_menu()

    def on_recording_error(self, error):
        logging.error("Requesting in-process audio recovery: %s", error)
        self.request_recovery()

    def request_recovery(self, icon=None, item=None):
        if self.controller.state in {"recording", "transcribing"}:
            if self.icon:
                self.icon.notify(
                    "Wait until recording or transcription finishes.",
                    "Whisper Right Ctrl",
                )
            return False
        requested = self.recovery.request()
        if requested and self.icon:
            self.icon.notify(
                "Reconnecting the microphone without reloading Whisper.",
                "Whisper Right Ctrl",
            )
        return requested

    def on_recovery_state_change(self, state):
        if state == "ready" and self.controller.paused:
            state = "paused"
        self.on_state_change(state)
        if self.icon:
            if state == "ready":
                self.icon.notify("Microphone is ready.", "Whisper Right Ctrl")
            elif state == "unavailable":
                self.icon.notify(
                    "Microphone is unavailable. Press Ctrl+Alt+F12 to try again.",
                    "Whisper Right Ctrl",
                )

    def status_label(self, item):
        labels = {
            "ready": "Status: Ready",
            "recording": "Status: Recording",
            "transcribing": "Status: Transcribing",
            "paused": "Status: Paused",
            "checking": "Status: Checking microphone",
            "reconnecting": "Status: Reconnecting microphone",
            "unavailable": "Status: Microphone unavailable",
        }
        return labels.get(self.current_state, f"Status: {self.current_state}")

    def monitor_resume(self):
        while not self.monitor_stop.wait(15):
            self.resume_monitor.tick(time.monotonic())

    def microphone_menu(self):
        return pystray.Menu(
            *[
                pystray.MenuItem(
                    device.name,
                    self.microphone_action(device),
                    checked=self.microphone_checked(device),
                    radio=True,
                )
                for device in self.microphones
            ]
        )

    def stop(self, icon=None, item=None):
        self.monitor_stop.set()
        if self.listener:
            self.listener.stop()
        if self.icon:
            self.icon.stop()

    def restart(self, icon=None, item=None):
        logging.info("Restart requested from tray menu")
        self.requested_exit_code = 75
        self.stop(icon, item)

    def run(self):
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
        menu = pystray.Menu(
            pystray.MenuItem(self.status_label, None, enabled=False),
            pystray.MenuItem("Reconnect microphone now (Ctrl+Alt+F12)", self.request_recovery),
            pystray.MenuItem("Microphone", self.microphone_menu()),
            pystray.MenuItem(
                "Recognition model",
                pystray.Menu(
                    *[
                        pystray.MenuItem(
                            label,
                            self.model_action(model),
                            checked=self.model_checked(model),
                            radio=True,
                        )
                        for model, label in MODEL_OPTIONS
                    ]
                ),
            ),
            pystray.MenuItem(self.pause_label, self.toggle_pause),
            pystray.MenuItem("Restart Whisper Right Ctrl", self.restart),
            pystray.MenuItem("Exit", self.stop),
        )
        self.icon = pystray.Icon("whisper-right-ctrl", make_icon(), "Whisper Right Ctrl — ready", menu)
        self.resume_monitor.tick(time.monotonic())
        threading.Thread(target=self.monitor_resume, name="resume-monitor", daemon=True).start()
        logging.info("Ready: hold Right Ctrl to record")
        self.icon.run()
        return self.requested_exit_code


def main() -> int:
    configure_logging()
    mutex = acquire_single_instance()
    if mutex is None:
        return 0
    try:
        return Application().run()
    except BaseException:
        logging.exception("Application crashed")
        return 1
    finally:
        kernel32 = ctypes.windll.kernel32
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle(mutex)


if __name__ == "__main__":
    raise SystemExit(main())
