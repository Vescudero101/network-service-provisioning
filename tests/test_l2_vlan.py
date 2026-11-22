import pytest

from nsp.errors import InputError
from nsp.services import l2_vlan
from nsp.utils.naming import normalise_interface_name


def test_interface_names_are_normalised():
    assert normalise_interface_name("gi0/1") == "Gi0/1"
    assert normalise_interface_name("GigabitEthernet0/1") == "Gi0/1"
    assert normalise_interface_name("Gi0/0.200") == "Gi0/0.200"


def test_build_service_intent_from_a_path():
    service_input = {"reference": "CUST1-V200", "vlan_id": 200}
    path = {"SW1": {"gi1/1": "access", "Gi0/1": {"mode": "trunk", "action": "remove"}}}
    data = l2_vlan.build_service_intent(service_input, {"vlan_name": "CUST1_V200"}, path)
    sw1 = data["devices"]["SW1"]
    assert sw1["vlans"][200]["vlan_name"] == "CUST1_V200"
    assert sw1["interfaces"]["Gi1/1"] == {"mode": "access", "vlan_id": 200}
    assert sw1["interfaces"]["Gi0/1"]["action"] == "remove"


def test_bad_port_mode_is_rejected():
    with pytest.raises(InputError):
        l2_vlan.build_service_intent({"reference": "X", "vlan_id": 1}, {}, {"SW1": {"Gi0/1": "hybrid"}})


def test_deploy_uses_the_placeholder_path_script():
    data = l2_vlan.deploy_intent({"reference": "X", "vlan_id": 200, "vlan_name": "CUST1_V200"}, None)
    assert list(data["devices"]) == ["SW1", "SW2"]
    for device in data["devices"].values():
        assert device["vlans"][200] == {"vlan_name": "CUST1_V200"}
        assert device["interfaces"] == {"Gi1/1": {"mode": "trunk", "vlan_id": 200}}


def test_cease_only_needs_the_vlan_id():
    cease_field_names = [field["name"] for field in l2_vlan.ACTIONS["cease"]["fields"]]
    assert cease_field_names == ["reference", "vlan_id"]
    data = l2_vlan.cease_intent({"reference": "X", "vlan_id": 200}, None)
    assert list(data["devices"]) == ["SW1", "SW2"]
