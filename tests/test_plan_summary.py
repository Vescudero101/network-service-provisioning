from nsp import settings
from nsp.job import create_job
from nsp.phases.summary import plan_text, summarise_plan, table_rows
from nsp.run_job import run_job
from nsp.services import l2_vlan
from tests.test_offline_run import EXAMPLES, load_yaml


def offline_job(name, service, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_DIR", tmp_path)
    user_input = load_yaml(EXAMPLES / name)
    user_input["service_type"] = service
    job = create_job(user_input, lambda phase, message: None, dry_run=True)
    run_job(job, None, lambda: False)
    return job


def test_summary_of_a_migration(tmp_path, monkeypatch):
    monkeypatch.setattr(l2_vlan, "build_new_path", lambda nr, vlan_id: {
        "SW1": {"Gi0/5": "trunk", "Gi0/1": {"mode": "trunk", "action": "remove"}},
    })
    job = offline_job("l2_vlan_input.yaml", "l2_vlan", tmp_path, monkeypatch)
    info = summarise_plan(job)["SW1"]
    actions = [(action, feature, name) for action, feature, name, _ in info["rows"]]
    assert ("add", "vlans", "200") in actions
    assert ("add", "interfaces", "Gi0/5") in actions
    assert ("remove", "interfaces", "Gi0/1") in actions
    assert info["added"] > 0 and info["removed"] == 2
    assert info["config"].index("! --- ADD ---") < info["config"].index("! --- REMOVE ---")


def test_table_has_one_row_per_device(tmp_path, monkeypatch):
    job = offline_job("l2_vlan_input.yaml", "l2_vlan", tmp_path, monkeypatch)
    rows = table_rows(summarise_plan(job))
    assert [row[0] for row in rows] == ["SW1", "SW2"]
    assert rows[0] == ("SW1", 5, 0, "vlans: +200  interfaces: +Gi1/1")


def test_table_shows_signs_for_add_and_remove(tmp_path, monkeypatch):
    monkeypatch.setattr(l2_vlan, "build_new_path", lambda nr, vlan_id: {
        "SW1": {"Gi0/5": "trunk", "Gi0/1": {"mode": "trunk", "action": "remove"}},
    })
    job = offline_job("l2_vlan_input.yaml", "l2_vlan", tmp_path, monkeypatch)
    assert table_rows(summarise_plan(job))[0][3] == "vlans: +200  interfaces: +Gi0/5, -Gi0/1"


def test_summary_of_l3vpn_uses_the_bgp_summary(tmp_path, monkeypatch):
    job = offline_job("l3vpn_input.yaml", "l3vpn", tmp_path, monkeypatch)
    rows = summarise_plan(job)["RTR1"]["rows"]
    assert ("add", "bgp", "neighbor 192.0.2.2") in [(a, f, n) for a, f, n, _ in rows]
    assert "router bgp 65000" in plan_text(job)
