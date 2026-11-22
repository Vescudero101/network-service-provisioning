"""A Job is one run of the tool. It carries all the data from phase to phase."""
import getpass
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from nsp import settings


def _ignore_phase_changes(phase, state):
    pass


@dataclass
class Job:
    user_input: dict
    folder: Path
    operator: str
    started_at: str
    report: object                      # function: report(phase, message)
    phase_changed: object = _ignore_phase_changes   # function: phase_changed(phase, state)
    dry_run: bool = False
    section_order: list = field(default_factory=lambda: ["add", "remove"])
    service_intent: dict = field(default_factory=dict)      # intent (what the user wants)
    resolved_intent: dict = field(default_factory=dict)     # intent + live values (set in PLAN)
    live_state: dict = field(default_factory=dict)        # parsed pre-check data
    problems: list = field(default_factory=list)
    plan: dict = field(default_factory=dict)              # {device: {"add": [lines], "remove": [lines]}}
    apply_started: bool = False
    status: str = "started"


def default_operator():
    return os.environ.get("OPERATOR") or getpass.getuser()


def _safe(text):
    """Make a string safe to use in a folder name."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(text))


def create_job(user_input, report, dry_run=False, phase_changed=None):
    started = datetime.now()
    name = "_".join([
        started.strftime("%Y%m%dT%H%M%S"),
        _safe(user_input.get("reference", "NOREF")),
        _safe(user_input.get("service_type", "service")),
        _safe(user_input.get("action", "action")),
    ])
    folder = settings.JOBS_DIR / name
    folder.mkdir(parents=True)
    report("INIT", f"Job folder: {folder}")
    return Job(
        user_input=user_input,
        folder=folder,
        operator=default_operator(),
        started_at=started.isoformat(timespec="seconds"),
        report=report,
        phase_changed=phase_changed or _ignore_phase_changes,
        dry_run=dry_run,
    )
