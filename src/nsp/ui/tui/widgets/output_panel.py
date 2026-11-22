"""The output of one phase (validation result, plan, apply result...)."""
from textual.widgets import Log


class OutputPanel(Log):
    def show(self, lines):
        self.clear()
        self.write_lines(lines if lines else ["(no output yet)"])
