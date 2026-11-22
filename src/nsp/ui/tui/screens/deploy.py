"""The deploy screen: the same for every service. Only the actions and their forms change.

    +----------------+--------------------------------------+
    | service        |                                      |
    | reference      |  1. choose: Deploy / Cease           |
    | operator 00:42 |  2. the form of that action          |
    | status         |  3. output of a phase, or the plan   |
    +----------------+  (the plan is a table: one row per   |
    | ✓ INIT         |   device, Enter opens its config)    |
    | ✓ DISCOVER     |                                      |
    | ▶ PLAN         |                                      |
    | · CONFIRM ...  |                                      |
    +----------------+                                      |
    | [Start]        |                                      |
    | [Dry run]      |                                      |
    | [Back] [Menu]  |                                      |
    +----------------+--------------------------------------+
         1fr                         3fr

The screen is a small state machine. The state decides which buttons are shown (ENABLED below).
Start does a real run (asks to confirm before pushing). Dry run stops after PLAN and pushes nothing.
"""
import time

from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ContentSwitcher, Footer, Header, Input, Label, ListItem, ListView

from nsp.errors import InputError
from nsp.job import default_operator
from nsp.phases.plan import has_changes
from nsp.phases.summary import summarise_plan
from nsp.services.registry import SERVICES
from nsp.ui.tui.screens.config import ConfigScreen
from nsp.ui.tui.widgets.action_bar import ActionBar
from nsp.ui.tui.widgets.job_status import JobStatus
from nsp.ui.tui.widgets.output_panel import OutputPanel
from nsp.ui.tui.widgets.phase_list import PhaseList
from nsp.ui.tui.widgets.plan_view import PlanView
from nsp.ui.tui.widgets.service_form import ServiceForm
from nsp.ui.tui.workers.job_runner import JobRunner

# state -> buttons the user can press
ENABLED = {
    "choose":       ["menu"],                            # Deploy or Cease?
    "form":         ["start", "dry_run", "back", "menu"],
    "busy":         [],                                  # a job thread is working: nothing to press
    "confirm":      ["apply", "cancel"],                 # the plan is on screen
    "stopped":      ["edit", "menu"],                    # failed before anything was pushed
    "apply_failed": ["rollback", "edit", "menu"],        # failed after config was pushed
    "cancelled":    ["edit", "menu"],
    "done":         ["edit", "menu"],
}


class DeployScreen(Screen):
    def __init__(self, service_name):
        super().__init__()
        self.service_name = service_name
        self.service = SERVICES[service_name]
        self.action = None                  # "deploy" or "cease", chosen first
        self.runner = None
        self.state = "choose"
        self.status_text = "Choose action"
        self.reset_run()

    def reset_run(self):
        self.job = None
        self.user_input = {}
        self.outputs = {}               # phase -> list of lines
        self.selected_phase = None
        self.failed_phase = None
        self.plan_ready = False         # True when the PLAN phase produced something to show
        self.started_at = None
        self.finished_at = None

    # ------------------------------------------------------------ layout
    def compose(self):
        yield Header()
        with Horizontal(id="deploy-body"):
            with Vertical(id="left-column"):
                yield JobStatus(id="job-status")
                yield PhaseList(id="phase-list")
                yield ActionBar(id="action-bar")
            with ContentSwitcher(initial="choose", id="main-area"):
                actions = self.service.ACTIONS
                yield ListView(
                    *[ListItem(Label(f"{a['label']}  -  {a['description']}"), name=key) for key, a in actions.items()],
                    id="choose",
                )
                for key, action in actions.items():
                    yield ServiceForm(action["fields"], id=f"form-{key}")
                yield OutputPanel(id="output")
                yield PlanView(id="plan")
        yield Footer()

    def on_mount(self):
        self.set_state("choose", self.status_text)
        self.query_one("#choose", ListView).focus()
        self.set_interval(1, self.refresh_status)       # keeps the elapsed time ticking

    def on_unmount(self):
        if self.runner:
            self.runner.answer(False)       # never leave the job thread waiting for a button

    # ------------------------------------------------------------ state
    def set_state(self, state, status_text):
        self.state = state
        self.status_text = status_text
        self.app.job_running = state == "busy"

        keys = ENABLED[state]
        if self.app.nr is None:             # offline: there are no devices to push to, only Dry run
            keys = [key for key in keys if key != "start"]
        self.query_one(ActionBar).enable(keys)
        self.refresh_status()

    def show(self, view_id):
        self.query_one("#main-area", ContentSwitcher).current = view_id

    def refresh_status(self):
        if self.started_at is None:
            elapsed = "-"
        else:
            seconds = int((self.finished_at or time.time()) - self.started_at)
            elapsed = f"{seconds // 60:02d}:{seconds % 60:02d}"

        title = self.service.TITLE
        if self.action:
            title += f" - {self.service.ACTIONS[self.action]['label']}"

        operator = self.job.operator if self.job else default_operator()
        self.query_one(JobStatus).show([
            title,
            self.user_input.get("reference", "-"),
            f"{operator}  {elapsed}",
            f"Status: {self.status_text}",
        ])

    def select_phase(self, phase):
        """Show the output of one phase. The PLAN phase gets the table once it is ready."""
        self.selected_phase = phase
        self.query_one(PhaseList).mark_selected(phase)
        if phase == "PLAN" and self.plan_ready:
            self.show("plan")
            self.query_one(PlanView).focus_table()
        else:
            self.query_one(OutputPanel).show(self.outputs.get(phase))
            self.show("output")

    # ------------------------------------------------------------ choose the action, then the form
    def on_list_view_selected(self, event):
        self.choose_action(event.item.name)

    def choose_action(self, action):
        self.action = action
        self.show(f"form-{action}")
        self.set_state("form", "Fill in the form")
        inputs = list(self.query_one(f"#form-{action}").query(Input))
        if inputs:
            inputs[0].focus()

    def go_back(self):
        """Back to 'Deploy or Cease?'"""
        self.action = None
        self.show("choose")
        self.set_state("choose", "Choose action")
        self.query_one("#choose", ListView).focus()

    # ------------------------------------------------------------ buttons
    def on_button_pressed(self, event):
        key = event.button.id.removeprefix("btn-")
        {
            "start": lambda: self.start_job(dry_run=False),
            "dry_run": lambda: self.start_job(dry_run=True),
            "apply": self.confirm_apply,
            "cancel": self.cancel_job,
            "rollback": self.start_rollback,
            "edit": self.edit_input,
            "back": self.go_back,
            "menu": self.go_to_menu,
        }[key]()

    def start_job(self, dry_run):
        try:
            values = self.query_one(f"#form-{self.action}", ServiceForm).get_values()
        except InputError as error:
            self.notify(str(error), severity="error")
            return

        values["service_type"] = self.service_name
        values["action"] = self.action
        self.clear_previous_run()
        self.user_input = values
        self.show("output")

        self.started_at = time.time()
        self.set_state("busy", "Dry run: pre-checks" if dry_run else "Running pre-checks")
        self.runner = JobRunner(self, self.app.nr, dry_run)
        self.runner.start(values)

    def confirm_apply(self):
        self.set_state("busy", "Applying config")
        self.runner.answer(True)

    def cancel_job(self):
        self.set_state("busy", "Cancelling")
        self.runner.answer(False)

    def start_rollback(self):
        self.set_state("busy", "Rolling back")
        self.runner.start_rollback()

    def edit_input(self):
        """Back to the form of the same action, with the values still in it."""
        self.clear_previous_run()
        self.show(f"form-{self.action}")
        self.set_state("form", "Edit the form")

    def go_to_menu(self):
        self.app.pop_screen()

    def clear_previous_run(self):
        self.reset_run()
        self.query_one(PhaseList).reset()
        self.query_one(PlanView).clear()
        self.query_one(OutputPanel).show(None)

    # ------------------------------------------------------------ the plan table
    def on_data_table_row_selected(self, event):
        device_name = event.row_key.value
        config = self.query_one(PlanView).config_of(device_name)
        self.app.push_screen(ConfigScreen(device_name, config))

    # ------------------------------------------------------------ called from the job thread
    # (through app.call_from_thread, so they run on the UI thread)
    def on_job_created(self, job):
        self.job = job
        self.refresh_status()

    def add_output(self, phase, message):
        self.outputs.setdefault(phase, []).extend(str(message).split("\n"))
        if phase == self.selected_phase and not (phase == "PLAN" and self.plan_ready):
            self.query_one(OutputPanel).show(self.outputs[phase])

    def on_phase_changed(self, phase, state):
        self.query_one(PhaseList).set_state(phase, state)
        if state == "running":
            self.select_phase(phase)                # follow the job
        elif state == "failed":
            self.failed_phase = phase
        elif state == "done" and phase == "PLAN" and self.job and has_changes(self.job):
            self.query_one(PlanView).show(summarise_plan(self.job))
            self.plan_ready = True
            if self.selected_phase == "PLAN":
                self.select_phase("PLAN")           # swap the plain output for the plan table

    def on_confirm_needed(self):
        self.query_one(PhaseList).set_state("CONFIRM", "waiting")
        self.set_state("confirm", "Review the plan")
        self.select_phase("PLAN")

    def on_job_finished(self, kind, message):
        self.finished_at = time.time()
        if kind != "done":
            phase = self.failed_phase or "INIT"
            self.add_output(phase, f"\nSTOPPED: {message}")
            self.select_phase(phase)

        if kind == "done":
            self.set_state("done", self.job.status if self.job else "done")
        elif kind == "cancelled":
            self.set_state("cancelled", "Cancelled. Nothing was pushed")
        elif kind == "apply_failed":
            self.set_state("apply_failed", "FAILED after config was pushed")
        else:
            self.set_state("stopped", f"Stopped in {self.failed_phase or 'INIT'}: nothing was pushed")

    def on_rollback_finished(self):
        self.set_state("apply_failed", "Rollback step finished: read its output")
        self.select_phase("ROLLBACK")

    def on_phase_label_selected(self, event):
        self.select_phase(event.phase)
