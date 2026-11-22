"""VLAN feature (finished example: copy this file when you write a new feature).

Data for one device looks like:
    {200: {"vlan_name": "CUST1_V200", "vni": 10200, "action": "add"}}

Every feature has these functions:
    fill_actions         give every item an explicit action
    split_by_action      -> (items to add, items to remove)
    commands_to_collect  which show commands DISCOVER and VERIFY need
    parse_output         raw show output -> simple dict ("live" data)
    validate             intent vs live data, BEFORE the change -> list of problems
    check_result         intent vs live data, AFTER the change -> list of problems

Optional (write them only when the feature needs them):
    resolve(items, live) -> items     fill in values that depend on the device (e.g. ACL sequence numbers)
    summarise(items) -> [(action, name, details)]     only if the items are not a plain {name: item} dict
"""
from nsp.utils.actions import fill_item_actions, split_items

IMPLEMENTED = True


def fill_actions(items, default_action):
    fill_item_actions(items, default_action)


def split_by_action(items):
    return split_items(items)


def commands_to_collect(items):
    return ["show vlan brief"]


def _split_ports(text):
    return [port.strip() for port in text.split(",") if port.strip()]


def parse_output(outputs):
    """Turn 'show vlan brief' into {200: {"name": "CUST1_V200", "ports": ["Gi1/1"]}}.
    Check this against your platform's real output (save it in tests/sample_outputs/)."""
    text = outputs.get("show vlan brief", "")
    vlans = {}
    current = None
    for line in text.splitlines():
        if line[:1].isdigit():
            parts = line.split(None, 3)             # id, name, status, ports
            current = int(parts[0])
            ports_text = parts[3] if len(parts) > 3 else ""
            vlans[current] = {"name": parts[1], "ports": _split_ports(ports_text)}
        elif current is not None and line.startswith(" ") and line.strip():
            vlans[current]["ports"] += _split_ports(line)    # ports continued on the next line
    return vlans


def validate(items, live, device_data):
    problems = []

    # Ports this same job is removing do not count as "still using the VLAN"
    ports_being_removed = [
        name for name, port in device_data.get("interfaces", {}).items()
        if port["action"] == "remove"
    ]

    for vlan_id, vlan in items.items():
        on_device = live.get(int(vlan_id))
        if vlan["action"] == "add":
            if on_device and on_device["name"] != vlan["vlan_name"]:
                problems.append(f"VLAN {vlan_id} already exists with a different name: {on_device['name']}")
        else:
            if not on_device:
                problems.append(f"VLAN {vlan_id} is not on the device, nothing to remove")
            else:
                ports_left = [p for p in on_device["ports"] if p not in ports_being_removed]
                if ports_left:
                    problems.append(f"VLAN {vlan_id} still has access ports: {ports_left}")
    return problems


def check_result(items, live):
    problems = []
    for vlan_id, vlan in items.items():
        on_device = live.get(int(vlan_id))
        if vlan["action"] == "add":
            if not on_device:
                problems.append(f"VLAN {vlan_id} is missing")
            elif on_device["name"] != vlan["vlan_name"]:
                problems.append(f"VLAN {vlan_id} has the wrong name: {on_device['name']}")
        elif on_device:
            problems.append(f"VLAN {vlan_id} is still present")
    return problems
