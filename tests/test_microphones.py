from whisper_right_ctrl.microphones import MicrophoneDevice, resolve_input_device


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
