# network-service-provisioning (nsp) v4

Provision network services (L2 VLAN, L3VPN, ...) with the same fixed phases every time:

    INIT -> DISCOVER -> VALIDATE -> SNAPSHOT -> PLAN -> CONFIRM -> APPLY -> VERIFY -> HEALTH CHECK -> RECORD

The Python package is `nsp` (`src/nsp`). Design decisions and the reasons behind them are in `docs/DESIGN.md`.

## Quick start

    python -m venv .venv && source .venv/bin/activate
    pip install -e ".[tui,dev]"          # Textual 8.2.x
    pytest

    # No devices needed: builds service_intent, renders config, stops after PLAN
    python -m nsp.main --service l2_vlan --input examples/l2_vlan_input.yaml --offline
    python -m nsp.main --service l2_vlan --input examples/l2_vlan_cease_input.yaml --offline   # stops at VALIDATE: see Status

    # Real devices, read-only (discover + validate + plan, nothing pushed)
    python -m nsp.main --service l2_vlan --input examples/l2_vlan_input.yaml --dry-run

    # Real deployment (asks for confirmation before pushing)
    python -m nsp.main --service l2_vlan --input examples/l2_vlan_input.yaml

    # Textual interface
    python -m nsp.main --tui --offline            # try it without devices (Dry run only)
    python -m nsp.main --tui                      # real devices

The input file has an `action`: `deploy` or `cease`. Before real devices: paste your NetBox inventory script into
`nornir_setup/__init__.py` (`init_nornir()` must return the `nr` object). Template folder names under `templates/` must
match your Nornir platform names. `pip install -e .` also creates a `network_service_provisioning.egg-info/` folder:
it is only package metadata and is ignored by git.

## The Textual interface

Run it inside `tmux` on the bastion (a dropped SSH session must not interrupt an APPLY). Terminal of at least 100x30.

- **Main menu:** services on the left (from `SERVICES`), on the right `ui/tui/info/general.md` (your
  "before you start" checklist: edit it) plus one `info/<service>.md` per service.
- **Deploy screen** (same for every service): left column = job info, the list of phases (click one to read its
  output) and the buttons; the rest of the screen is the main area.
- **Flow:** 1) choose **Deploy** or **Cease** (each has its own form), 2) fill in the form, 3) **Start** or **Dry run**.
  Start runs INIT to PLAN and stops at the plan; Apply then runs APPLY, VERIFY and HEALTH CHECK. A run also stops by
  itself when a check fails and jumps to the phase that failed.
- **Dry run** is chosen for each run with its own button (there is no global setting). It stops after PLAN and pushes
  nothing. Offline (no devices) only Dry run is offered.
- **The plan** is a table with one row per device (lines added/removed, items). Up/Down to choose a device, Enter opens
  the config that will be pushed to it full screen, Esc comes back. The full config is always saved in `rendered_config/`.
- **Buttons** (left column, only the ones that make sense now are shown): Start, Dry run, Apply, Cancel, Rollback,
  Edit (back to the form), Back (back to Deploy/Cease), Menu. No Cancel while config is being pushed, and the app
  refuses to quit during a job.
- **Rollback** is a button, never automatic (and not written yet: it shows where the backups are).

Every run creates a folder under `jobs/` (named with the time, reference, service and action) with the input,
`service_intent.yaml`, `resolved_intent.yaml`, pre/post checks, backups, rendered config and `audit.json`.

## Where things live

| Folder | What it is | Changes when... |
|---|---|---|
| `services/` | One file per service type, with its actions (deploy, cease) and their forms. List in `services/registry.py` | you add a service |
| `services/l2_vlan_paths.py` | **Placeholders** for your two path scripts (dummy data for now) | you plug in your scripts |
| `features/` | Reusable blocks (vlans, interfaces, vrfs, bgp). List and order in `features/registry.py` | a service needs something new |
| `templates/<platform>/` | Config snippets, one per feature | you add a vendor |
| `phases/` | The generic workflow steps (`summary.py` builds the plan table, `health_check.py` holds the health checks) | rarely |
| `tasks/` | Nornir tasks: the only code that talks to devices | rarely |
| `nornir_setup/` | Your NetBox script that builds the `nr` object | you change the inventory source |
| `ui/` | `cli.py` and the Textual app in `ui/tui/`. Phases never print or ask questions | you change the UI |

## Plug in your path scripts (L2 VLAN)

`services/l2_vlan_paths.py` has two functions. Both only read, and both return `{device: {port: mode}}`:

- `build_new_path(nr, vlan_id)`: DEPLOY, creates the path for a new VLAN.
- `find_existing_path(nr, vlan_id)`: CEASE, finds where the VLAN is today.

They return dummy data now (SW1 and SW2, VLAN on the trunk Gi1/1) and INIT prints a DUMMY warning while
`IS_DUMMY = True`. Set it to `False` when both are real.

## Add a new service
1. Create `services/my_service.py` with `TITLE` and `ACTIONS`: for `deploy` and `cease`, a label, a description, the
   form `fields` and a `create_service_intent(service_input, nr)` function (see `services/l2_vlan.py`).
2. Add it to `SERVICES` in `services/registry.py`.
3. If it needs a feature that does not exist yet, add `features/<name>.py` + `templates/<platform>/<name>.j2`
   and register it in `features/registry.py` (`FEATURES` and `FEATURE_ORDER`).
4. Add `ui/tui/info/<service>.md`. Run `pytest`: `tests/test_registry.py` checks that nothing is missing.

## Add a feature
Copy `features/vlans.py` (the finished example). Required functions: `fill_actions`, `split_by_action`,
`commands_to_collect`, `parse_output`, `validate`, `check_result`. Optional: `resolve` (values that depend on the
device, e.g. ACL sequence numbers) and `summarise` (only if the items are not a plain `{name: item}` dict).
Set `IMPLEMENTED = True` when the checks are written.

## Add a health check
Write a function `check(device_name, nr) -> list of problems` and add it to `HEALTH_CHECKS` in
`phases/health_check.py`. It runs on every device of the job, after VERIFY, whatever the service. With no checks
written the phase is shown as skipped (`-`), never as a tick.

## Safety rules built in
- Features with `IMPLEMENTED = False` (stubs) are refused at APPLY: no config is pushed without checks.
- Backups in `jobs/` are full configs (needed for rollback) with owner-only permissions. They must never be copied
  to the audit repo: only `audit.json` and the intent files go there.
- Rollback is not automated: the backups are saved, restore is manual for now (see `phases/rollback.py`).
- A failed health check stops the job after the config was pushed, so the TUI offers Rollback (same as a failed VERIFY).
- Offline (no `nr`) can never reach APPLY, even if a run is started without the dry-run flag.

## Status
Working and tested headless (45 tests): INIT, DISCOVER, VALIDATE, PLAN, CONFIRM, job folders, audit record, VLAN
feature, offline mode, the action choice and forms, the plan table, per-run dry run, the whole Textual interface.
The L2 VLAN path scripts are placeholders with dummy data.
Written but never run on devices: `tasks/` (collect, backup, push), APPLY and VERIFY. HEALTH CHECK has no checks yet.
Offline cease stops at VALIDATE ("VLAN is not on the device"): offline there is no live state to find the VLAN in.
TODO: interfaces/vrfs/bgp checks, apply-until-converged retry loop, the health checks, ROLLBACK, "net changes only"
in the plan (skip lines that are already on the device), L3VPN cease form, grouping identical devices in the plan table.
