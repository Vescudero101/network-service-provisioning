"""The list of service types. To add a service: new file in this folder + one line below."""
from nsp.services import l2_vlan, l3vpn

SERVICES = {
    "l2_vlan": l2_vlan,
    "l3vpn": l3vpn,
}
