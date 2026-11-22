"""BGP feature (SKELETON: checks not written yet).

Data for one device is ONE block with a list of neighbours:
    {"local_as": 65000, "vrf": "CUST1",
     "neighbors": {"192.0.2.2": {"remote_as": 65100, "description": "CUST1", "action": "add"}}}

TODO: parse_output (show bgp ... summary), validate (neighbour not already configured),
check_result (session Established, only the expected prefixes received).
Set IMPLEMENTED = True when done.
"""
from nsp.utils.actions import fill_item_actions

IMPLEMENTED = False


def fill_actions(items, default_action):
    fill_item_actions(items["neighbors"], default_action)


def split_by_action(items):
    neighbors = items["neighbors"]
    neighbors_to_add = {ip: n for ip, n in neighbors.items() if n["action"] == "add"}
    neighbors_to_remove = {ip: n for ip, n in neighbors.items() if n["action"] == "remove"}
    to_add = dict(items, neighbors=neighbors_to_add) if neighbors_to_add else {}
    to_remove = dict(items, neighbors=neighbors_to_remove) if neighbors_to_remove else {}
    return to_add, to_remove


def summarise(items):
    """The items are not a plain {name: item} dict, so the PLAN summary needs this."""
    rows = []
    for ip, neighbor in items["neighbors"].items():
        details = f"remote_as={neighbor['remote_as']} vrf={items['vrf']} local_as={items['local_as']}"
        rows.append((neighbor["action"], f"neighbor {ip}", details))
    return rows


def commands_to_collect(items):
    return ["show ip bgp vpnv4 all summary"]


def parse_output(outputs):
    return {}       # TODO


def validate(items, live, device_data):
    return []       # TODO


def check_result(items, live):
    return []       # TODO
