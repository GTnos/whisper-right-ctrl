from whisper_right_ctrl.microphones import (
    deduplicate_input_devices,
    MicrophoneDevice,
    filter_working_input_devices,
    resolve_input_device,
)


def test_resolve_input_device_follows_name_when_windows_changes_index():
    devices = [
        MicrophoneDevice(index=2, name="Oculus Virtual Microphone", channels=1),
        MicrophoneDevice(index=7, name="Microphone (Logitech Webcam C925e)", channels=2),
    ]

    selected = resolve_input_device(
        devices,
        preferred_index=2,
        preferred_name="Microphone (Logitech Webcam C925e)",
    )

    assert selected == devices[1]


def test_unusable_microphones_are_removed_from_the_menu_candidates():
    devices = [
        MicrophoneDevice(index=3, name="Broken microphone", channels=1),
        MicrophoneDevice(index=7, name="Working microphone", channels=2),
    ]

    working = filter_working_input_devices(
        devices,
        can_open=lambda device: device.index == 7,
    )

    assert working == [devices[1]]


def test_duplicate_interfaces_for_one_microphone_are_shown_once():
    devices = [
        MicrophoneDevice(index=12, name="Microphone (Logitech Webcam C925e)", channels=2),
        MicrophoneDevice(index=30, name="Microphone (Logitech Webcam C925e)", channels=2),
        MicrophoneDevice(index=8, name="Steam Streaming Microphone", channels=8),
    ]

    visible = deduplicate_input_devices(devices, preferred_index=30)

    assert visible == [devices[1], devices[2]]
