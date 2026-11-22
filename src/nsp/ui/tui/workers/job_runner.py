"""Runs run_job in a background thread, so the screen stays alive while Nornir works.

The thread never touches widgets. It calls screen methods through app.call_from_thread().
ask_confirm() blocks the thread until the user presses a button.
"""
import threading

from nsp.errors import JobCancelled
from nsp.job import create_job
from nsp.phases.rollback import rollback
from nsp.run_job import run_job


class JobRunner:
    def __init__(self, screen, nr, dry_run):
        self.screen = screen
        self.nr = nr
        self.dry_run = dry_run
        self.job = None
        self._answer = False
        self._answered = threading.Event()

    # ----- called from the UI thread -----
    def start(self, user_input):
        self.screen.run_worker(lambda: self._run(user_input), thread=True,
                               exclusive=True, exit_on_error=False, name="job")

    def start_rollback(self):
        self.screen.run_worker(self._rollback, thread=True,
                               exclusive=True, exit_on_error=False, name="rollback")

    def answer(self, approved):
        """Called by the buttons (and when the screen closes, to release a waiting thread)."""
        self._answer = approved
        self._answered.set()

    # ----- called from the worker thread -----
    def _call(self, function, *args):
        self.screen.app.call_from_thread(function, *args)

    def report(self, phase, message):
        self._call(self.screen.add_output, phase, message)

    def phase_changed(self, phase, state):
        self._call(self.screen.on_phase_changed, phase, state)

    def ask_confirm(self):
        self._answered.clear()
        self._call(self.screen.on_confirm_needed)
        self._answered.wait()
        return self._answer

    def _run(self, user_input):
        kind, message = "done", ""
        try:
            self.job = create_job(user_input, self.report, self.dry_run, self.phase_changed)
            self._call(self.screen.on_job_created, self.job)
            run_job(self.job, self.nr, self.ask_confirm)
        except JobCancelled as error:
            kind, message = "cancelled", str(error)
        except Exception as error:
            pushed = self.job is not None and self.job.apply_started
            kind = "apply_failed" if pushed else "stopped"
            message = str(error) or error.__class__.__name__
        self._call(self.screen.on_job_finished, kind, message)

    def _rollback(self):
        self.phase_changed("ROLLBACK", "running")
        try:
            rollback(self.job, self.nr)
            self.phase_changed("ROLLBACK", "done")
        except Exception as error:
            self.report("ROLLBACK", f"FAILED: {error}")
            self.phase_changed("ROLLBACK", "failed")
        self._call(self.screen.on_rollback_finished)
