from __future__ import annotations

import ctypes
import logging
import sys
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
from whisper_right_ctrl.config import app_data_dir, load_config, log_path, save_config
from whisper_right_ctrl.controller import PushToTalkController
from whisper_right_ctrl.microphones import (
    MicrophoneDevice,
    deduplicate_input_devices,
    filter_working_input_devices,
    list_input_devices,
    resolve_input_device,
)


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
        self.controller = PushToTalkController(
            recorder=SoundDeviceRecorder(
                self.config.input_device,
                fallback_devices=fallback_devices,
                on_device_changed=self.on_recorder_device_changed,
            ),
            transcriber=transcriber,
            converter=TraditionalChineseConverter(),
            inserter=ClipboardInserter(self.config.restore_clipboard),
            minimum_seconds=self.config.minimum_seconds,
            on_state_change=self.on_state_change,
        )

    def on_state_change(self, state):
        logging.info("State: %s", state)
        colors = {"ready": "#16A34A", "recording": "#DC2626", "transcribing": "#D97706", "paused": "#6B7280"}
        if state == "recording":
            winsound.Beep(880, 45)
        elif state == "transcribing":
            winsound.Beep(660, 45)
        if self.icon:
            self.icon.icon = make_icon(colors.get(state, "#6B7280"))
            self.icon.title = f"Whisper Right Ctrl — {state}"
            self.icon.update_menu()

    def on_press(self, key):
        if key == keyboard.Key.ctrl_r:
            self.controller.press()

    def on_release(self, key):
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
        if self.listener:
            self.listener.stop()
        if self.icon:
            self.icon.stop()

    def run(self):
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
        menu = pystray.Menu(
            pystray.MenuItem("Microphone", self.microphone_menu()),
            pystray.MenuItem(self.pause_label, self.toggle_pause),
            pystray.MenuItem("Exit", self.stop),
        )
        self.icon = pystray.Icon("whisper-right-ctrl", make_icon(), "Whisper Right Ctrl — ready", menu)
        logging.info("Ready: hold Right Ctrl to record")
        self.icon.run()


def main() -> int:
    configure_logging()
    mutex = acquire_single_instance()
    if mutex is None:
        return 0
    try:
        Application().run()
        return 0
    except BaseException:
        logging.exception("Application crashed")
        return 1
    finally:
        kernel32 = ctypes.windll.kernel32
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle(mutex)


if __name__ == "__main__":
    raise SystemExit(main())
