"""The buttons, one per line under the phase list. Only the ones that make sense now are shown."""
from textual.containers import Vertical
from textual.widgets import Button

BUTTONS = [
    ("start", "Start", "primary"),
    ("dry_run", "Dry run", "primary"),
    ("apply", "Apply", "success"),
    ("cancel", "Cancel", "warning"),
    ("rollback", "Rollback", "error"),
    ("edit", "Edit", "default"),
    ("back", "Back", "default"),
    ("menu", "Menu", "default"),
]


class ActionBar(Vertical):
    def compose(self):
        for key, label, variant in BUTTONS:
            yield Button(label, id=f"btn-{key}", variant=variant, compact=True)

    def enable(self, keys):
        """Buttons that are not allowed now are disabled AND hidden (so Tab skips them too)."""
        for key, _, _ in BUTTONS:
            button = self.query_one(f"#btn-{key}", Button)
            button.disabled = key not in keys
            button.display = key in keys
