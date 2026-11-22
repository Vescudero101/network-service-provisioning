"""Service: L3VPN customer handoff on one PE (DUMMY: shows the shape, adjust to your design).

Deploy and cease use the same form for now: removing the service needs the same details to render the
removal. When you have a discovery script for L3VPN, give "cease" a shorter form like l2_vlan.py does.

User input (see examples/l3vpn_input.yaml):
    reference, action (deploy|cease), vrf_name, rd, device, interface, vlan_id,
    ip_address (e.g. 192.0.2.1/30), local_as, neighbor_ip, remote_as
"""
import ipaddress

from nsp.utils.naming import normalise_interface_name

TITLE = "L3VPN"

FIELDS = [
    {"name": "reference", "label": "Service reference", "kind": "text", "placeholder": "CUST1-L3VPN"},
    {"name": "vrf_name", "label": "VRF name", "kind": "text"},
    {"name": "rd", "label": "Route distinguisher", "kind": "text", "placeholder": "65000:200"},
    {"name": "device", "label": "PE device", "kind": "text", "placeholder": "RTR1"},
    {"name": "interface", "label": "Interface (sub-interface)", "kind": "text", "placeholder": "Gi0/0.200"},
    {"name": "vlan_id", "label": "VLAN ID", "kind": "int"},
    {"name": "ip_address", "label": "PE IP address with prefix", "kind": "text", "placeholder": "192.0.2.1/30"},
    {"name": "local_as", "label": "Local AS", "kind": "int"},
    {"name": "neighbor_ip", "label": "Customer neighbour IP", "kind": "text", "placeholder": "192.0.2.2"},
    {"name": "remote_as", "label": "Customer AS", "kind": "int"},
]

SECTION_ORDER = ["add", "remove"]


def create_service_intent(service_input, nr):
    address = ipaddress.ip_interface(service_input["ip_address"])
    interface_name = normalise_interface_name(service_input["interface"])

    return {
        "service": {
            "type": "l3vpn",
            "reference": service_input["reference"],
        },
        "devices": {
            service_input["device"]: {
                "vrfs": {
                    service_input["vrf_name"]: {"rd": service_input["rd"]},
                },
                "interfaces": {
                    interface_name: {
                        "mode": "routed",
                        "vlan_id": int(service_input["vlan_id"]),
                        "vrf": service_input["vrf_name"],
                        "ip": str(address.ip),
                        "mask": str(address.netmask),
                    },
                },
                "bgp": {
                    "local_as": int(service_input["local_as"]),
                    "vrf": service_input["vrf_name"],
                    "neighbors": {
                        service_input["neighbor_ip"]: {
                            "remote_as": int(service_input["remote_as"]),
                            "description": service_input["reference"],
                        },
                    },
                },
            },
        },
    }


# The same form and the same intent function for both actions (see the note at the top)
ACTIONS = {
    "deploy": {"label": "Deploy", "description": "create the VRF, interface and BGP neighbour",
               "fields": FIELDS, "create_service_intent": create_service_intent},
    "cease": {"label": "Cease", "description": "remove the VRF, interface and BGP neighbour",
              "fields": FIELDS, "create_service_intent": create_service_intent},
}
