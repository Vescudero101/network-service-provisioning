"""TUI tests: Textual runs headless, a 'pilot' presses the buttons. No devices needed."""
import asyncio

import pytest

pytest.importorskip("textual")

from textual.widgets import Button, DataTable, Input, Log       # noqa: E402

from nsp import settings                                        # noqa: E402
from nsp.ui.tui.app import NspApp                               # noqa: E402
from nsp.ui.tui.screens.config import ConfigScreen              # noqa: E402
from nsp.ui.tui.screens.deploy import DeployScreen              # noqa: E402
from nsp.ui.tui.workers import job_runner                       # noqa: E402

SIZE = (120, 40)
FAKE_NR = object()      # "devices are connected": the tests that use it replace run_job, so nothing touches it


def fill_deploy_form(screen):
    form = screen.query_one("#form-deploy")
    form.query_one("#field-reference", Input).value = "CUST1-V200"
    form.query_one("#field-vlan_id", Input).value = "200"
    form.query_one("#field-vlan_name", Input).value = "CUST1_V200"


def fill_cease_form(screen):
    form = screen.query_one("#form-cease")
    form.query_one("#field-reference", Input).value = "CUST1-V200"
    form.query_one("#field-vlan_id", Input).value = "200"


def enabled_buttons(screen):
    return sorted(button.id.removeprefix("btn-") for button in screen.query(Button) if not button.disabled)


def visible_buttons(screen):
    return sorted(button.id.removeprefix("btn-") for button in screen.query(Button) if button.display)


def output_text(screen, phase):
    return "\n".join(screen.outputs.get(phase, []))


def run(coroutine_function, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "JOBS_DIR", tmp_path)
    asyncio.run(coroutine_function())


async def open_deploy_screen(pilot, action="deploy"):
    """Main menu -> first service (L2 VLAN) -> choose the action."""
    await pilot.press("enter")                       # first service in the menu: L2 VLAN
    await pilot.pause()
    if action == "cease":
        await pilot.press("down")
    await pilot.press("enter")                       # choose Deploy (first) or Cease (second)
    await pilot.pause()
    return pilot.app.screen


async def wait_for_state(pilot, screen, state):
    for _ in range(50):
        await pilot.pause(0.05)
        if screen.state == state:
            return
    raise AssertionError(f"screen never reached '{state}', it is in '{screen.state}'")


# ---------------------------------------------------------------- choose the action first
def test_action_is_chosen_before_the_form(monkeypatch, tmp_path):
    async def scenario():
        app = NspApp(None)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.press("enter")
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, DeployScreen) and screen.state == "choose"
            assert visible_buttons(screen) == ["menu"]

            await pilot.press("enter")               # Deploy
            await pilot.pause()
            assert screen.state == "form" and screen.action == "deploy"
            assert {"vlan_name"} <= {i.id.removeprefix("field-") for i in screen.query_one("#form-deploy").query(Input)}

            await pilot.click("#btn-back")
            await pilot.pause()
            assert screen.state == "choose" and screen.action is None
    run(scenario, monkeypatch, tmp_path)


def test_cease_form_only_asks_for_reference_and_vlan_id(monkeypatch, tmp_path):
    async def scenario():
        app = NspApp(None)
        async with app.run_test(size=SIZE) as pilot:
            screen = await open_deploy_screen(pilot, "cease")
            assert screen.action == "cease"
            ids = [widget.id for widget in screen.query_one("#form-cease").query(Input)]
            assert ids == ["field-reference", "field-vlan_id"]
    run(scenario, monkeypatch, tmp_path)


# ---------------------------------------------------------------- dry run is chosen for each run
def test_offline_only_dry_run_is_possible(monkeypatch, tmp_path):
    async def scenario():
        app = NspApp(None)
        async with app.run_test(size=SIZE) as pilot:
            screen = await open_deploy_screen(pilot)
            assert enabled_buttons(screen) == ["back", "dry_run", "menu"]      # no Start without devices
            assert visible_buttons(screen) == ["back", "dry_run", "menu"]      # and the others are hidden
    run(scenario, monkeypatch, tmp_path)


def test_with_devices_both_start_and_dry_run_are_offered(monkeypatch, tmp_path):
    async def scenario():
        app = NspApp(FAKE_NR)
        async with app.run_test(size=SIZE) as pilot:
            screen = await open_deploy_screen(pilot)
            assert enabled_buttons(screen) == ["back", "dry_run", "menu", "start"]
    run(scenario, monkeypatch, tmp_path)


def test_dry_run_button_stops_after_the_plan(monkeypatch, tmp_path):
    async def scenario():
        app = NspApp(None)
        async with app.run_test(size=SIZE) as pilot:
            screen = await open_deploy_screen(pilot)
            fill_deploy_form(screen)
            await pilot.click("#btn-dry_run")
            await app.workers.wait_for_complete()
            await pilot.pause()

            assert screen.state == "done"
            assert screen.job.dry_run is True
            assert "vlan 200" in output_text(screen, "PLAN")
            assert enabled_buttons(screen) == ["edit", "menu"]
            assert "DUMMY" in output_text(screen, "INIT")             # the placeholder data is announced
    run(scenario, monkeypatch, tmp_path)


def test_start_button_is_a_real_run_and_dry_run_is_not_remembered(monkeypatch, tmp_path):
    runs = []

    def fake_run_job(job, nr, ask_confirm):
        runs.append(job.dry_run)
        job.status = "success"
        return job

    monkeypatch.setattr(job_runner, "run_job", fake_run_job)

    async def scenario():
        app = NspApp(FAKE_NR)
        async with app.run_test(size=SIZE) as pilot:
            screen = await open_deploy_screen(pilot)
            fill_deploy_form(screen)
            await pilot.click("#btn-dry_run")
            await app.workers.wait_for_complete()
            await pilot.pause()
            await pilot.click("#btn-edit")
            await pilot.pause()
            await pilot.click("#btn-start")
            await app.workers.wait_for_complete()
            await pilot.pause()
    run(scenario, monkeypatch, tmp_path)
    assert runs == [True, False]


def test_empty_form_is_refused(monkeypatch, tmp_path):
    async def scenario():
        app = NspApp(None)
        async with app.run_test(size=SIZE) as pilot:
            screen = await open_deploy_screen(pilot)
            await pilot.click("#btn-dry_run")
            await pilot.pause()
            assert screen.state == "form"                    # nothing started
            assert not list(tmp_path.iterdir())              # no job folder was created
    run(scenario, monkeypatch, tmp_path)


def test_validation_failure_stops_and_shows_why(monkeypatch, tmp_path):
    async def scenario():
        app = NspApp(None)
        async with app.run_test(size=SIZE) as pilot:
            screen = await open_deploy_screen(pilot, "cease")
            fill_cease_form(screen)                          # offline: VLAN is not "on the device"
            await pilot.click("#btn-dry_run")
            await app.workers.wait_for_complete()
            await pilot.pause()

            assert screen.state == "stopped"
            assert "not on the device" in output_text(screen, "VALIDATE")
            assert enabled_buttons(screen) == ["edit", "menu"]
            assert screen.selected_phase == "VALIDATE"       # the screen jumped to the problem
    run(scenario, monkeypatch, tmp_path)


# ---------------------------------------------------------------- confirm / apply / rollback
def fake_run_job(outcome):
    """Stand-in for run_job: walks the confirm step, then succeeds, fails or is cancelled."""
    def run_job(job, nr, ask_confirm):
        for phase in ("INIT", "DISCOVER", "VALIDATE", "SNAPSHOT", "PLAN"):
            job.phase_changed(phase, "running")
            job.report(phase, f"{phase} output")
            job.phase_changed(phase, "done")
        job.phase_changed("CONFIRM", "running")
        if not ask_confirm():
            job.phase_changed("CONFIRM", "failed")
            from nsp.errors import JobCancelled
            raise JobCancelled("Cancelled at the confirm step.")
        job.phase_changed("CONFIRM", "done")
        job.apply_started = True
        job.phase_changed("APPLY", "running")
        if outcome == "apply_fails":
            job.phase_changed("APPLY", "failed")
            raise RuntimeError("VLAN 200 is missing on SW2")
        job.phase_changed("APPLY", "done")
        job.phase_changed("HEALTH_CHECK", "skipped")
        job.status = "success"
        return job
    return run_job


def drive_confirm_flow(monkeypatch, tmp_path, outcome, button):
    monkeypatch.setattr(job_runner, "run_job", fake_run_job(outcome))
    result = {}

    async def scenario():
        app = NspApp(FAKE_NR)
        async with app.run_test(size=SIZE) as pilot:
            screen = await open_deploy_screen(pilot)
            fill_deploy_form(screen)
            await pilot.click("#btn-start")
            await wait_for_state(pilot, screen, "confirm")
            result["at_confirm"] = (screen.state, enabled_buttons(screen), screen.selected_phase)

            await pilot.click(f"#btn-{button}")
            await app.workers.wait_for_complete()
            await pilot.pause()
            result["screen"] = screen
            result["final"] = (screen.state, enabled_buttons(screen))
            result["quit_blocked_during_job"] = app.job_running
            label = screen.query_one("#phase-HEALTH_CHECK")      # read it while the app is still running
            result["health_label"] = (label.state, str(label.render()))

    run(scenario, monkeypatch, tmp_path)
    return result


def test_confirm_then_apply_succeeds(monkeypatch, tmp_path):
    result = drive_confirm_flow(monkeypatch, tmp_path, "ok", "apply")
    assert result["at_confirm"] == ("confirm", ["apply", "cancel"], "PLAN")
    assert result["final"] == ("done", ["edit", "menu"])
    assert result["quit_blocked_during_job"] is False


def test_skipped_health_check_is_not_shown_as_a_tick(monkeypatch, tmp_path):
    result = drive_confirm_flow(monkeypatch, tmp_path, "ok", "apply")
    assert result["health_label"] == ("skipped", "- HEALTH CHECK")


def test_cancel_at_confirm(monkeypatch, tmp_path):
    result = drive_confirm_flow(monkeypatch, tmp_path, "ok", "cancel")
    assert result["final"] == ("cancelled", ["edit", "menu"])


def test_failed_apply_offers_rollback(monkeypatch, tmp_path):
    result = drive_confirm_flow(monkeypatch, tmp_path, "apply_fails", "apply")
    assert result["final"] == ("apply_failed", ["edit", "menu", "rollback"])
    assert "VLAN 200 is missing on SW2" in output_text(result["screen"], "APPLY")


def test_rollback_button_runs_the_rollback_step(monkeypatch, tmp_path):
    monkeypatch.setattr(job_runner, "run_job", fake_run_job("apply_fails"))

    async def scenario():
        app = NspApp(FAKE_NR)
        async with app.run_test(size=SIZE) as pilot:
            screen = await open_deploy_screen(pilot)
            fill_deploy_form(screen)
            await pilot.click("#btn-start")
            await wait_for_state(pilot, screen, "confirm")
            await pilot.click("#btn-apply")
            await app.workers.wait_for_complete()
            await pilot.pause()
            await pilot.click("#btn-rollback")
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert screen.selected_phase == "ROLLBACK"
            assert "NOT automatic yet" in output_text(screen, "ROLLBACK")
            assert screen.state == "apply_failed"            # the user can still choose what to do next
    run(scenario, monkeypatch, tmp_path)


# ---------------------------------------------------------------- the plan table
def test_plan_table_has_one_row_per_device_and_enter_opens_the_config(monkeypatch, tmp_path):
    from nsp.ui.tui.widgets.plan_view import PlanView

    async def scenario():
        app = NspApp(None)
        async with app.run_test(size=SIZE) as pilot:
            screen = await open_deploy_screen(pilot)
            fill_deploy_form(screen)
            await pilot.click("#btn-dry_run")
            await app.workers.wait_for_complete()
            await pilot.pause()

            assert screen.plan_ready
            table = screen.query_one(PlanView).query_one(DataTable)
            assert table.row_count == 2                              # SW1 and SW2 from the placeholder path
            assert table.get_row("SW1")[:3] == ["SW1", 5, 0]

            await pilot.press("down", "enter")                       # second row: SW2
            await pilot.pause()
            assert isinstance(app.screen, ConfigScreen)
            assert app.screen.device_name == "SW2"
            config = "\n".join(app.screen.query_one(Log).lines)
            assert "vlan 200" in config and "switchport trunk allowed vlan add 200" in config

            await pilot.press("escape")                              # back to the plan
            await pilot.pause()
            assert app.screen is screen

            # run again from the same screen: the table must not pile up old rows
            await pilot.click("#btn-edit")
            await pilot.pause()
            await pilot.click("#btn-dry_run")
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert screen.query_one(PlanView).query_one(DataTable).row_count == 2
    run(scenario, monkeypatch, tmp_path)
