"""Whole workflow without devices: input -> service_intent -> rendered config."""
from pathlib import Path

import pytest

from nsp import settings
from nsp.errors import InputError, ValidationFailed
from nsp.job import create_job
from nsp.run_job import run_job
from nsp.services import l2_vlan
from nsp.utils.yaml_tools import load_yaml

EXAMPLES = Path(__file__).parents[1] / "examples"


def run_example(name, service, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_DIR", tmp_path)
    user_input = load_yaml(EXAMPLES / name)
    user_input["service_type"] = service
    return run_offline(user_input)


def run_offline(user_input):
    job = create_job(user_input, lambda phase, message: None, dry_run=True)
    return run_job(job, None, lambda: False)


def test_l2_vlan_deploy_offline_gives_config_for_sw1_and_sw2(tmp_path, monkeypatch):
    job = run_example("l2_vlan_input.yaml", "l2_vlan", tmp_path, monkeypatch)
    assert job.status == "dry run: stopped after plan"
    for device in ("SW1", "SW2"):
        config = (job.folder / "rendered_config" / f"{device}.txt").read_text()
        assert "vlan 200" in config and " name CUST1_V200" in config
        assert "interface Gi1/1" in config and "switchport trunk allowed vlan add 200" in config
    assert (job.folder / "audit.json").exists()
    assert job.folder.name.endswith("_l2_vlan_deploy")


def test_l2_vlan_cease_offline_stops_at_validate(tmp_path, monkeypatch):
    # Offline there is no live state, so the VLAN is "not on the device": the check must say so
    with pytest.raises(ValidationFailed, match="not on the device"):
        run_example("l2_vlan_cease_input.yaml", "l2_vlan", tmp_path, monkeypatch)


def test_cease_removes_from_the_trunk_before_the_vlan(tmp_path, monkeypatch):
    monkeypatch.setattr("nsp.features.vlans.validate", lambda items, live, device_data: [])    # skip the live check
    job = run_example("l2_vlan_cease_input.yaml", "l2_vlan", tmp_path, monkeypatch)
    assert job.plan["SW1"]["add"] == []
    assert job.plan["SW1"]["remove"] == [
        "interface Gi1/1", " switchport trunk allowed vlan remove 200", "no vlan 200",
    ]


def test_migration_adds_before_removing(tmp_path, monkeypatch):
    # The path script may return a port to remove next to a port to add
    monkeypatch.setattr(l2_vlan, "build_new_path", lambda nr, vlan_id: {
        "SW1": {"Gi0/5": "trunk", "Gi0/1": {"mode": "trunk", "action": "remove"}},
    })
    job = run_example("l2_vlan_input.yaml", "l2_vlan", tmp_path, monkeypatch)
    assert job.plan["SW1"]["add"][-1].startswith(" switchport trunk allowed vlan add 200")
    assert job.plan["SW1"]["remove"] == ["interface Gi0/1", " switchport trunk allowed vlan remove 200"]
    assert job.section_order == ["add", "remove"]


def test_l3vpn_offline(tmp_path, monkeypatch):
    job = run_example("l3vpn_input.yaml", "l3vpn", tmp_path, monkeypatch)
    lines = job.plan["RTR1"]["add"]
    assert lines[0] == "vrf definition CUST1"                 # vrfs first
    assert "router bgp 65000" in lines                        # bgp last
    assert " ip address 192.0.2.1 255.255.255.252" in lines


def test_missing_input_field_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_DIR", tmp_path)
    with pytest.raises(InputError, match="Missing input fields"):
        run_offline({"service_type": "l2_vlan", "action": "deploy", "reference": "X"})


def test_unknown_action_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_DIR", tmp_path)
    with pytest.raises(InputError, match="Unknown action"):
        run_offline({"service_type": "l2_vlan", "action": "add", "reference": "X"})
