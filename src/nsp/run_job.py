"""The runner: the whole workflow, readable top to bottom.

It never prints and never asks questions itself. The UI gives it:
    job.report(phase, message)          show progress text
    job.phase_changed(phase, state)     state is "running", "done", "failed" or "skipped"
    ask_confirm()                       returns True or False

Rollback is NOT automatic: if the job fails after config was pushed, the error is raised and
the UI decides what to do (the TUI shows a Rollback button).
"""
from nsp.errors import JobCancelled
from nsp.phases import health_check as health_check_phase
from nsp.phases.apply import apply_config
from nsp.phases.confirm import confirm
from nsp.phases.discover import discover
from nsp.phases.initialize import initialize
from nsp.phases.plan import has_changes, plan
from nsp.phases.record import record
from nsp.phases.snapshot import snapshot
from nsp.phases.validate import validate
from nsp.phases.verify import verify


def run_phase(job, name, function, *args):
    """Run one phase and tell the UI when it starts and how it ended."""
    job.phase_changed(name, "running")
    try:
        function(job, *args)
    except Exception:
        job.phase_changed(name, "failed")
        raise
    job.phase_changed(name, "done")


def run_job(job, nr, ask_confirm):
    try:
        run_phase(job, "INIT", initialize, nr)
        run_phase(job, "DISCOVER", discover, nr)
        run_phase(job, "VALIDATE", validate)
        run_phase(job, "SNAPSHOT", snapshot, nr)
        run_phase(job, "PLAN", plan, nr)

        if not has_changes(job):
            job.status = "nothing to change"
            return job

        if job.dry_run or nr is None:       # no devices (offline) can never be pushed to
            job.status = "dry run: stopped after plan"
            job.report("PLAN", "Dry run: nothing was pushed")
            return job

        run_phase(job, "CONFIRM", confirm, ask_confirm)

        job.apply_started = True
        run_phase(job, "APPLY", apply_config, nr)
        run_phase(job, "VERIFY", verify, nr)

        if health_check_phase.HEALTH_CHECKS:
            run_phase(job, "HEALTH_CHECK", health_check_phase.health_check, nr)
        else:
            job.phase_changed("HEALTH_CHECK", "skipped")
            job.report("HEALTH_CHECK", "Skipped: no health checks are written yet. Nothing was checked.")

        job.status = "success"
        return job

    except JobCancelled:
        job.status = "cancelled"
        raise
    except Exception as error:
        job.status = f"failed: {error}"
        raise
    finally:
        record(job)
