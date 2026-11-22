import pytest

from nsp.errors import InputError
from nsp.utils.actions import fill_item_actions


def test_action_is_always_the_last_key():
    items = {
        "Gi0/1": {"mode": "trunk", "vlan_id": 344},                      # gets the default
        "Gi0/3": {"mode": "trunk", "action": "remove", "vlan_id": 344},  # had it in the middle
    }
    fill_item_actions(items, "add")
    assert list(items["Gi0/1"]) == ["mode", "vlan_id", "action"]
    assert list(items["Gi0/3"]) == ["mode", "vlan_id", "action"]
    assert items["Gi0/3"]["action"] == "remove"


def test_bad_action_is_rejected():
    with pytest.raises(InputError):
        fill_item_actions({"Gi0/1": {"mode": "trunk", "action": "ad"}}, "add")
