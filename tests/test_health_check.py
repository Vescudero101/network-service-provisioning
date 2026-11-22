"""HEALTH CHECK runs after VERIFY. The phases are replaced by stubs here: only the flow is tested."""
import pytest

from nsp import settings
from nsp import run_job as run_job_module
from nsp.errors import HealthCheckFailed
from nsp.job import create_job
from nsp.phases import health_check as health_check_phase


def stub_phases(monkeypatch):
    def initialize(job, nr):
        job.service_intent = {"devices": {"SW1": {}, "SW2": {}}}

    def nothing(job, *args):
        pass

    monkeypatch.setattr(run_job_module, "initialize", initialize)
    for name in ("discover", "validate", "snapshot", "plan", "apply_config", "verify"):
        monkeypatch.setattr(run_job_module, name, nothing)
    monkeypatch.setattr(run_job_module, "has_changes", lambda job: True)


def run_with_stubs(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "JOBS_DIR", tmp_path)
    stub_phases(monkeypatch)
    events = []
    job = create_job({"service_type": "x", "action": "deploy", "reference": "R"},
                     lambda phase, message: events.append(("report", phase, message)),
                     dry_run=False, phase_changed=lambda phase, state: events.append((phase, state)))
    return job, events


def test_phase_comes_after_verify_and_is_skipped_without_checks(monkeypatch, tmp_path):
    job, events = run_with_stubs(monkeypatch, tmp_path)
    run_job_module.run_job(job, object(), lambda: True)
    states = [event for event in events if event[0] in ("VERIFY", "HEALTH_CHECK")]
    assert states == [("VERIFY", "running"), ("VERIFY", "done"), ("HEALTH_CHECK", "skipped")]
    assert job.status == "success"


def test_checks_run_on_every_device(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(health_check_phase, "HEALTH_CHECKS", [lambda device, nr: seen.append(device) or []])
    job, events = run_with_stubs(monkeypatch, tmp_path)
    run_job_module.run_job(job, object(), lambda: True)
    assert seen == ["SW1", "SW2"]
    assert ("HEALTH_CHECK", "done") in events and job.status == "success"


def test_failed_check_stops_the_job_after_apply(monkeypatch, tmp_path):
    monkeypatch.setattr(health_check_phase, "HEALTH_CHECKS", [lambda device, nr: ["CPU is 95%"]])
    job, events = run_with_stubs(monkeypatch, tmp_path)
    with pytest.raises(HealthCheckFailed, match="SW1: CPU is 95%"):
        run_job_module.run_job(job, object(), lambda: True)
    assert ("HEALTH_CHECK", "failed") in events
    assert job.apply_started                  # so the TUI offers Rollback
