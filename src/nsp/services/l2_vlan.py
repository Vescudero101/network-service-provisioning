"""Service: L2 VLAN across a switched path.

Two actions, each with its own form (the user picks the action first):
    deploy   form: reference, vlan_id, vlan_name      path: build_new_path() from services/l2_vlan_paths.py
    cease    form: reference, vlan_id                 path: find_existing_path() (where is the VLAN today?)

The path scripts are PLACEHOLDERS for now (dummy data: SW1 and SW2, VLAN on the trunk Gi1/1).
"""
from nsp.errors import InputError
from nsp.services import l2_vlan_paths
from nsp.services.l2_vlan_paths import build_new_path, find_existing_path
from nsp.utils.naming import normalise_interface_name

TITLE = "L2 VLAN"
USES_DUMMY_DATA = l2_vlan_paths.IS_DUMMY

# add first, then remove = make-before-break. For L2 where a loop is a risk, use ["remove", "add"].
SECTION_ORDER = ["add", "remove"]


def build_service_intent(service_input, vlan, path):
    """Path + VLAN -> service intent. Used by both actions."""
    vlan_id = int(service_input["vlan_id"])
    service_intent = {
        "service": {"type": "l2_vlan", "reference": service_input["reference"]},
        "devices": {},
    }

    for device_name, ports in path.items():
        interfaces = {}
        for port_name, port in ports.items():
            # "Gi0/1: trunk"  or  "Gi0/1: {mode: trunk, action: remove}"
            port = {"mode": port} if isinstance(port, str) else dict(port)
            if port.get("mode") not in ("access", "trunk"):
                raise InputError(f"{device_name} {port_name}: mode must be access or trunk")
            port["vlan_id"] = vlan_id
            interfaces[normalise_interface_name(port_name)] = port

        service_intent["devices"][device_name] = {
            "vlans": {vlan_id: dict(vlan)},
            "interfaces": interfaces,
        }
    return service_intent


def deploy_intent(service_input, nr):
    path = build_new_path(nr, int(service_input["vlan_id"]))
    return build_service_intent(service_input, {"vlan_name": service_input["vlan_name"]}, path)


def cease_intent(service_input, nr):
    path = find_existing_path(nr, int(service_input["vlan_id"]))
    return build_service_intent(service_input, {}, path)


# What the TUI draws: one form per action. kind: text | int | select. required defaults to True.
REFERENCE_FIELD = {"name": "reference", "label": "Service reference", "kind": "text", "placeholder": "CUST1-V200"}
VLAN_ID_FIELD = {"name": "vlan_id", "label": "VLAN ID", "kind": "int"}

ACTIONS = {
    "deploy": {
        "label": "Deploy",
        "description": "create the VLAN and its path",
        "fields": [
            REFERENCE_FIELD,
            VLAN_ID_FIELD,
            {"name": "vlan_name", "label": "VLAN name", "kind": "text"},
        ],
        "create_service_intent": deploy_intent,
    },
    "cease": {
        "label": "Cease",
        "description": "find where the VLAN is and remove it",
        "fields": [
            REFERENCE_FIELD,
            VLAN_ID_FIELD,
        ],
        "create_service_intent": cease_intent,
    },
}
