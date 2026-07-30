from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Callable, Iterable


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


def can_open_input_device(device: MicrophoneDevice, sample_rate: int = 16000) -> bool:
    import sounddevice as sd

    stream = None
    try:
        stream = sd.InputStream(
            device=device.index,
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        )
        stream.start()
        stream.stop()
        return True
    except BaseException as error:
        logging.info(
            "Hiding unavailable input device [%s] %s: %s",
            device.index,
            device.name,
            error,
        )
        return False
    finally:
        if stream is not None:
            try:
                stream.close()
            except BaseException:
                pass


def filter_working_input_devices(
    devices: Iterable[MicrophoneDevice],
    can_open: Callable[[MicrophoneDevice], bool] = can_open_input_device,
) -> list[MicrophoneDevice]:
    return [device for device in devices if can_open(device)]


def deduplicate_input_devices(
    devices: Iterable[MicrophoneDevice],
    preferred_index: int | str | None = None,
) -> list[MicrophoneDevice]:
    available = list(devices)
    preferred = [device for device in available if device.index == preferred_index]
    ordered = [*preferred, *(device for device in available if device.index != preferred_index)]
    visible = []
    seen_names = set()
    for device in ordered:
        identity = device.name.casefold().strip()
        if identity in seen_names:
            continue
        seen_names.add(identity)
        visible.append(device)
    return visible


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
