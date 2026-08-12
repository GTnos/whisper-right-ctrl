from whisper_right_ctrl.adapters import SoundDeviceRecorder


class Stream:
    def __init__(self):
        self.started = False

    def start(self):
        self.started = True

    def close(self):
        pass

    def stop(self):
        self.started = False


def test_recorder_falls_back_when_the_saved_audio_interface_cannot_open():
    attempted = []
    selected = []
    fallback_stream = Stream()

    def create_stream(**options):
        attempted.append(options["device"])
        if options["device"] == 12:
            raise RuntimeError("DirectSound error")
        return fallback_stream

    recorder = SoundDeviceRecorder(
        device=12,
        fallback_devices=[30],
        on_device_changed=selected.append,
        stream_factory=create_stream,
    )

    recorder.start()

    assert attempted == [12, 30]
    assert fallback_stream.started
    assert recorder.device == 30
    assert selected == [30]


def test_recorder_recovery_resets_audio_backend_and_probes_microphone():
    events = []
    stream = Stream()
    recorder = SoundDeviceRecorder(
        device=12,
        stream_factory=lambda **options: stream,
        backend_reset=lambda: events.append("reset"),
    )

    recorder.recover()

    assert events == ["reset"]
    assert not stream.started
    assert recorder._stream is None
