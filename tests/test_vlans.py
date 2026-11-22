"""Feature tests use saved device output: no devices needed."""
from pathlib import Path

from nsp.features import vlans

SAMPLE = Path(__file__).parent / "sample_outputs" / "show_vlan_brief.txt"


def live_state():
    return vlans.parse_output({"show vlan brief": SAMPLE.read_text()})


def test_parse_output():
    live = live_state()
    assert live[200]["name"] == "CUST1_V200"
    assert live[200]["ports"] == ["Gi1/1", "Gi1/2"]      # second port was on a continuation line
    assert live[300]["ports"] == []


def test_add_ok_when_same_name_already_exists():
    items = {200: {"vlan_name": "CUST1_V200", "action": "add"}}
    assert vlans.validate(items, live_state(), {}) == []


def test_add_fails_when_name_differs():
    items = {200: {"vlan_name": "SOMETHING_ELSE", "action": "add"}}
    assert len(vlans.validate(items, live_state(), {})) == 1


def test_remove_fails_when_ports_still_use_it():
    items = {200: {"vlan_name": "CUST1_V200", "action": "remove"}}
    assert len(vlans.validate(items, live_state(), {})) == 1


def test_remove_ok_when_this_job_removes_the_ports():
    items = {200: {"vlan_name": "CUST1_V200", "action": "remove"}}
    device_data = {"interfaces": {"Gi1/1": {"action": "remove"}, "Gi1/2": {"action": "remove"}}}
    assert vlans.validate(items, live_state(), device_data) == []


def test_check_result_reports_missing_vlan():
    items = {999: {"vlan_name": "NEW", "action": "add"}}
    assert vlans.check_result(items, live_state()) == ["VLAN 999 is missing"]
