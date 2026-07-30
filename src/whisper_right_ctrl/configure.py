from __future__ import annotations

import sys

from .config import load_config, save_config
from .microphones import list_input_devices


def main() -> int:
    devices = list_input_devices()
    if not devices:
        print("No microphone input device was found.")
        return 1
    print("\nAvailable microphone devices:\n")
    for device in devices:
        print(f"  [{device.index}] {device.name} ({device.channels} input channel(s))")
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
        if any(device.index == selected for device in devices):
            break
        print("That device is not an available microphone.")
    current.input_device = selected
    name = next(device.name for device in devices if device.index == selected)
    current.input_device_name = name
    path = save_config(current)
    print(f"\nSaved microphone: [{selected}] {name}")
    print(f"Configuration: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
