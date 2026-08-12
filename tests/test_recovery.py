import threading

from whisper_right_ctrl.recovery import RecoveryCoordinator, RecoveryHotkey, ResumeMonitor


def test_recovery_runs_once_in_process_and_reports_visible_states():
    entered = threading.Event()
    release = threading.Event()
    states = []

    def recover():
        entered.set()
        release.wait(1)

    coordinator = RecoveryCoordinator(recover, states.append)

    assert coordinator.request()
    assert entered.wait(1)
    assert not coordinator.request()
    release.set()
    assert coordinator.wait(1)
    assert states == ["reconnecting", "ready"]


def test_ctrl_alt_f12_requests_recovery_but_plain_f12_does_not():
    requests = []
    hotkey = RecoveryHotkey(lambda: requests.append("recover"))

    hotkey.press("f12")
    hotkey.release("f12")
    hotkey.press("ctrl_l")
    hotkey.press("alt_l")
    hotkey.press("f12")
    hotkey.press("f12")
    hotkey.release("f12")
    hotkey.release("alt_l")
    hotkey.release("ctrl_l")

    assert requests == ["recover"]


def test_resume_monitor_requests_recovery_after_a_long_clock_gap():
    requests = []
    monitor = ResumeMonitor(lambda: requests.append("recover"), expected_interval=15)

    monitor.tick(100)
    monitor.tick(115)
    monitor.tick(190)

    assert requests == ["recover"]
