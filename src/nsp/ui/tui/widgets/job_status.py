"""Top of the left column: a few lines about the job."""
from textual.widgets import Static


class JobStatus(Static):
    def __init__(self, **kwargs):
        super().__init__("", markup=False, **kwargs)

    def show(self, lines):
        self.update("\n".join(lines))
