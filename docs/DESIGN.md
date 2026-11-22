# Design notes (read this first when continuing the project)

## Purpose
A team tool (network-service-provisioning, package `nsp`) to deploy network services on Cisco (Juniper later) devices from a bastion, with a Textual TUI.
Inventory comes from NetBox through the user's own script that builds a Nornir object. The tool is **stateless**:
nothing about a service is stored between runs; devices and NetBox are the source of truth. Each run writes a
job folder with everything it did (that is the audit trail, not a database).

## Vocabulary
- **Service:** what a customer has (L2 VLAN, L3VPN). One file in `services/` per type.
- **Feature:** reusable building block (vlans, interfaces, vrfs, bgp). A device gets only the features it needs.
- **Job:** one run of the tool for one service. One folder under `jobs/` per job.
- **Service reference:** the single identifier the user types (e.g. `CUST1-V200`). Replaces customer + change ID.
- **service_intent:** what the user wants (device > feature > items, each item with `add`/`remove`, always the last key).
- **resolved_intent:** service_intent plus values that depend on the live device (e.g. next ACL sequence).
- **Section:** `add` and `remove` work inside one job; order is per service (`SECTION_ORDER`, default add then remove).

## Flow
INIT (user input -> service_intent) > DISCOVER (one SSH session per device, read-only) > VALIDATE (intent vs live
state) > SNAPSHOT (full config backup) > PLAN (resolve + render templates + summary) > CONFIRM (user) > APPLY (push
per section, check each section) > VERIFY (final check) > HEALTH CHECK (general device health, independent of the
service) > RECORD (always). `phases/` are plain functions
`(job, nr)`; `run_job.py` calls them in order; `run_phase` reports start/end to the UI.

The user picks an action first (**deploy** or **cease**); each action has its own form. Internally every item
is `add` or `remove` (deploy = add, cease = remove). The path of an L2 VLAN comes from the user's own scripts
(`services/l2_vlan_paths.py`, placeholders with dummy data for now), called in INIT because the intent needs the devices.

## Decisions and why
| Decision | Reason |
|---|---|
| Own pipeline (plain functions), no Prefect/GitLab CI/Itential | Interactive tool on one bastion, no extra services to run. Phases take plain data, so an orchestrator could wrap them later |
| One generic workflow, solutions plug in | A new service = one function that builds the intent + maybe a new feature. Phases never change |
| Fixed phases; extra steps go inside a phase | Same screen, logs and audit for every service. Skipping phases was rejected as unsafe |
| Features have the same functions (see `features/vlans.py`) | collect, parse, validate, check_result written once per feature, reused by every service |
| Verify the RESULT, not the pushed commands | The device may silently apply only part of a config; check state and re-apply the gap |
| All show commands collected in one session per device | SSH logins are slow; features only declare what they need |
| Core never prints or asks; UI passes `report`, `ask_confirm`, `phase_changed` | CLI and Textual share the same core; TUI runs `run_job` in a thread |
| Rollback is a button, never automatic | Engineer decides after seeing what failed. Backups are saved before APPLY |
| `registry.py` files, empty `__init__.py` | Explicit and easy to find; `tests/test_registry.py` catches missing parts |
| No class hierarchy for services/phases | Modules + dictionary are enough; revisit only with a concrete problem (many services, shared logic) |
| Full config backups never leave the bastion | Running configs can contain secrets (SNMP, type 7, keys). Audit repo gets audit.json + intents only |
| Plan = table with one row per device, config full screen on Enter | Works for 1 or 20 devices: the overview stays short, line counts flag surprises, config one keypress away. Collapsible blocks per device were rejected (too long at 10-20 devices); grouping identical devices (C) is a possible later add-on |
| Action (deploy / cease) is chosen before the form; one form per action | Cease only needs the VLAN ID (the path script finds the rest); a single form with an "action" field asked for too much |
| Dry run is a button for each run (Start / Dry run), not a global setting | Nothing sticky to forget or leave on; offline only Dry run is offered |
| Buttons are in the left column under the phase list, only the valid ones shown | The output area gets the full height; fewer buttons to read at each step |
| HEALTH CHECK is the last phase, after VERIFY, and shown as skipped while no checks exist | Same checks for every service. A tick on a check that does not exist would mislead |
| Path scripts are placeholders that return dummy data, announced by a warning in INIT | The rest of the pipeline can be run and tested now; nobody mistakes dummy data for real discovery |

## Working agreements with the user
- The user is a senior network engineer, **not a Python developer**: simple, readable code; plain functions and dicts;
  spell names out (`service`, not `srvc`); explain anything non-obvious.
- Complexity levels the user can ask for: **L1** plain script/functions, **L2** (default) functions + a few
  dataclasses, **L3** classes/registries/tests/logging. Be clinical: go up a level only when it clearly pays off and say why.
- Cisco IOS-XE first; Juniper later (templates + parsers per platform, same intent files).
- Don't claim something works on devices unless it was run on devices.

## Status
Tested headless: everything except device access. Never run on devices: `tasks/`, APPLY, VERIFY.
Placeholders: the L2 VLAN path scripts (dummy data). HEALTH CHECK exists but has no checks yet.
TODO: interfaces/vrfs/bgp checks (features with `IMPLEMENTED = False` are refused at APPLY), apply-until-converged
retry loop, the health checks, ROLLBACK, net-changes-only plan, L3VPN cease form, Juniper, grouping identical devices
in the plan table (offline cease also has no live state to find the VLAN in).
