import time

import numpy as np

from whisper_right_ctrl.controller import PushToTalkController, clean_transcript


class Recorder:
    def __init__(self, samples=8000):
        self.audio = np.ones(samples, dtype=np.float32)
        self.starts = 0
        self.stops = 0

    def start(self):
        self.starts += 1

    def stop(self):
        self.stops += 1
        return self.audio


def wait_for(predicate):
    deadline = time.monotonic() + 1
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("timed out")


def build(samples=8000):
    recorder = Recorder(samples)
    inserted = []
    controller = PushToTalkController(
        recorder=recorder,
        transcriber=lambda audio: "明天油漆进场",
        converter=lambda text: text.replace("进", "進").replace("场", "場"),
        inserter=inserted.append,
    )
    return controller, recorder, inserted


def test_duplicate_press_starts_once():
    controller, recorder, _ = build()
    assert controller.press()
    assert not controller.press()
    assert recorder.starts == 1


def test_release_without_press_is_ignored():
    controller, recorder, _ = build()
    assert not controller.release()
    assert recorder.stops == 0


def test_short_recording_is_ignored():
    controller, _, inserted = build(samples=100)
    controller.press()
    controller.release()
    wait_for(lambda: controller.state == "ready")
    assert inserted == []


def test_transcript_is_converted_and_inserted():
    controller, _, inserted = build()
    controller.press()
    controller.release()
    wait_for(lambda: inserted and controller.state == "ready")
    assert inserted == ["明天油漆進場"]


def test_clean_transcript_normalizes_whitespace():
    assert clean_transcript("  first\n\nsecond  ") == "first second"


def test_recording_failure_requests_application_recovery():
    class BrokenRecorder:
        def start(self):
            raise RuntimeError("audio interface stopped after sleep")

        def stop(self):
            return np.empty(0, dtype=np.float32)

    errors = []
    controller = PushToTalkController(
        recorder=BrokenRecorder(),
        transcriber=lambda audio: "",
        converter=lambda text: text,
        inserter=lambda text: None,
        on_recording_error=errors.append,
    )

    assert not controller.press()
    assert len(errors) == 1
    assert str(errors[0]) == "audio interface stopped after sleep"
