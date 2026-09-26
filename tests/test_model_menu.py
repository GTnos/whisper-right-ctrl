import threading

from whisper_right_ctrl import app
from whisper_right_ctrl.config import AppConfig


class TrayIcon:
    def __init__(self):
        self.notifications = []
        self.menu_updates = 0

    def notify(self, message, title):
        self.notifications.append((message, title))

    def update_menu(self):
        self.menu_updates += 1


def test_selecting_model_saves_next_launch_choice_and_explains_restart(monkeypatch):
    application = app.Application.__new__(app.Application)
    application.config = AppConfig(model="turbo")
    saved = []
    monkeypatch.setattr(app, "save_config", lambda config: saved.append(config.model))
    icon = TrayIcon()

    application.model_action("large-v3")(icon, None)

    assert application.config.model == "large-v3"
    assert saved == ["large-v3"]
    assert icon.menu_updates == 1
    assert icon.notifications == [
        (
            "High accuracy - large-v3 will be used after restarting Whisper Right Ctrl. "
            "The first launch downloads several GB of model data.",
            "Whisper Right Ctrl",
        )
    ]


def test_current_model_is_marked_in_menu():
    application = app.Application.__new__(app.Application)
    application.config = AppConfig(model="large-v3")

    assert application.model_checked("large-v3")(None)
    assert not application.model_checked("turbo")(None)


def test_restart_requests_supervised_relaunch_and_stops_current_instance():
    application = app.Application.__new__(app.Application)
    application.monitor_stop = threading.Event()
    application.listener = None
    application.icon = TrayIcon()
    application.icon.stop = lambda: setattr(application.icon, "stopped", True)
    application.requested_exit_code = 0

    application.restart()

    assert application.requested_exit_code == 75
    assert application.monitor_stop.is_set()
    assert application.icon.stopped
