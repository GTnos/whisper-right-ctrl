from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MicrophoneDevice:
    index: int
    name: str
    channels: int


def list_input_devices() -> list[MicrophoneDevice]:
    import sounddevice as sd

    return [
        MicrophoneDevice(index, str(device["name"]), int(device["max_input_channels"]))
        for index, device in enumerate(sd.query_devices())
        if int(device["max_input_channels"]) > 0
    ]


def resolve_input_device(
    devices: Iterable[MicrophoneDevice],
    preferred_index: int | str | None,
    preferred_name: str | None,
) -> MicrophoneDevice | None:
    available = list(devices)
    if preferred_name:
        for device in available:
            if device.index == preferred_index and device.name == preferred_name:
                return device
        for device in available:
            if device.name == preferred_name:
                return device
    for device in available:
        if device.index == preferred_index:
            return device
    return None
