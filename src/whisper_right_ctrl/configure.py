from __future__ import annotations

import sys

from .config import AppConfig, load_config, save_config


def input_devices():
    import sounddevice as sd

    result = []
    for index, device in enumerate(sd.query_devices()):
        if int(device["max_input_channels"]) > 0:
            result.append((index, str(device["name"]), int(device["max_input_channels"])))
    return result


def main() -> int:
    devices = input_devices()
    if not devices:
        print("No microphone input device was found.")
        return 1
    print("\nAvailable microphone devices:\n")
    for index, name, channels in devices:
        print(f"  [{index}] {name} ({channels} input channel(s))")
    current = load_config()
    default = current.input_device
    prompt = f"\nMicrophone number [{default if default is not None else 'required'}]: "
    while True:
        value = input(prompt).strip()
        if not value and default is not None:
            selected = default
            break
        try:
            selected = int(value)
        except ValueError:
            print("Enter one of the device numbers shown above.")
            continue
        if any(index == selected for index, _, _ in devices):
            break
        print("That device is not an available microphone.")
    current.input_device = selected
    path = save_config(current)
    name = next(name for index, name, _ in devices if index == selected)
    print(f"\nSaved microphone: [{selected}] {name}")
    print(f"Configuration: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
