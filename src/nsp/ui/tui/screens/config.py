"""One device's config, full screen and read only. Esc (or q) goes back to the plan."""
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Log


class ConfigScreen(Screen):
    BINDINGS = [("escape", "close", "Back to the plan"), ("q", "close", "Back to the plan")]

    def __init__(self, device_name, config):
        super().__init__()
        self.device_name = device_name
        self.config = config

    def compose(self):
        yield Header()
        yield Label(f"{self.device_name}: config that will be pushed (read only). Esc to go back.", id="config-title")
        yield Log(highlight=False, id="config-text")
        yield Footer()

    def on_mount(self):
        log = self.query_one(Log)
        log.write_lines(self.config.splitlines())
        log.focus()

    def action_close(self):
        self.app.pop_screen()
