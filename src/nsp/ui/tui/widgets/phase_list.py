"""The phases as a vertical list in the left column. Click one to read its output."""
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static

from nsp.phase_names import PHASES

SYMBOLS = {"pending": "·", "running": "▶", "waiting": "?", "done": "✓", "failed": "✗", "skipped": "-"}


class PhaseLabel(Static):
    class Selected(Message):
        def __init__(self, phase):
            super().__init__()
            self.phase = phase

    def __init__(self, phase, **kwargs):
        super().__init__(f"{SYMBOLS['pending']} {phase.replace('_', ' ')}", **kwargs)
        self.phase = phase
        self.state = "pending"
        self.add_class("pending")

    def set_state(self, state):
        self.remove_class(self.state)
        self.state = state
        self.add_class(state)
        self.update(f"{SYMBOLS[state]} {self.phase.replace('_', ' ')}")

    def on_click(self):
        self.post_message(self.Selected(self.phase))


class PhaseList(Vertical):
    def compose(self):
        for phase in PHASES:
            yield PhaseLabel(phase, id=f"phase-{phase}")
        rollback = PhaseLabel("ROLLBACK", id="phase-ROLLBACK")
        rollback.display = False                    # only shown if the user presses Rollback
        yield rollback

    def set_state(self, phase, state):
        label = self.query_one(f"#phase-{phase}", PhaseLabel)
        label.display = True
        label.set_state(state)

    def mark_selected(self, phase):
        for label in self.query(PhaseLabel):
            label.set_class(label.phase == phase, "selected")

    def reset(self):
        for label in self.query(PhaseLabel):
            label.set_state("pending")
            label.remove_class("selected")
        self.query_one("#phase-ROLLBACK", PhaseLabel).display = False
