"""Textual app. Install with: pip install -e ".[tui]"

    python -m nsp.main --tui              (real devices)
    python -m nsp.main --tui --offline    (try it without devices: Dry run only, stops after PLAN)

Rule: the core (run_job, phases) never imports Textual. The TUI only talks to it through
job.report(), job.phase_changed() and ask_confirm() (see workers/job_runner.py).
Run it inside tmux on the bastion: if your SSH connection drops during APPLY, tmux keeps it alive.
"""
from textual.app import App

from nsp.ui.tui.screens.main_menu import MainMenuScreen


class NspApp(App):
    CSS_PATH = "styles.tcss"
    TITLE = "nsp - network service provisioning"

    def __init__(self, nr):
        super().__init__()
        self.nr = nr                    # None = offline: only Dry run is possible
        self.job_running = False        # True while a job is working: quitting is blocked

        if nr is None:
            self.sub_title = "OFFLINE: no devices, Dry run only"

    def on_mount(self):
        self.push_screen(MainMenuScreen())

    async def action_quit(self):
        if self.job_running:
            self.notify("A job is running. Wait until it finishes.", severity="warning")
            return
        self.exit()
