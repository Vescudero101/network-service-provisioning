"""VRF feature (SKELETON: checks not written yet).

Data for one device looks like:
    {"CUST1": {"rd": "65000:200", "action": "add"}}

TODO: parse_output (show vrf), validate (name and RD not used by another VRF), check_result.
Set IMPLEMENTED = True when done.
"""
from nsp.utils.actions import fill_item_actions, split_items

IMPLEMENTED = False


def fill_actions(items, default_action):
    fill_item_actions(items, default_action)


def split_by_action(items):
    return split_items(items)


def commands_to_collect(items):
    return ["show vrf"]


def parse_output(outputs):
    return {}       # TODO


def validate(items, live, device_data):
    return []       # TODO


def check_result(items, live):
    return []       # TODO
