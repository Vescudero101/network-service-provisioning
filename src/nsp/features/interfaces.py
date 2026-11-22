"""Interfaces feature (SKELETON: checks not written yet).

Data for one device looks like:
    {"Gi0/1": {"mode": "trunk", "vlan_id": 200, "action": "add"},
     "Gi1/1": {"mode": "access", "vlan_id": 200}}
    {"Gi0/0.200": {"mode": "routed", "vlan_id": 200, "vrf": "CUST1", "ip": "192.0.2.1", "mask": "255.255.255.252"}}

TODO: parse_output (show interfaces trunk / status), validate (port exists, port free, trunk allows VLAN),
check_result (port is in the VLAN, trunk allowed list contains it). Verify the RESULT, not the literal command.
Set IMPLEMENTED = True when done.
"""
from nsp.utils.actions import fill_item_actions, split_items

IMPLEMENTED = False


def fill_actions(items, default_action):
    fill_item_actions(items, default_action)


def split_by_action(items):
    return split_items(items)


def commands_to_collect(items):
    return ["show interfaces trunk", "show interfaces status"]


def parse_output(outputs):
    return {}       # TODO


def validate(items, live, device_data):
    return []       # TODO


def check_result(items, live):
    return []       # TODO
