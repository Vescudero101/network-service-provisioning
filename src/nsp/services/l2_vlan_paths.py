"""PLACEHOLDERS: dummy data until your two scripts are plugged in. Nothing here talks to a device.

Replace the body of each function with a call to your script. They only READ (the intent is built
in INIT, before anything is pushed). Each function returns the L2 path as a dictionary:

    {device: {port: mode}}                         mode is "trunk" or "access"
    {device: {port: {"mode": "trunk", "action": "remove"}}}      (optional: one port with its own action)

nr is the Nornir object (None when the tool runs offline). Set IS_DUMMY = False when both are real:
that removes the DUMMY warning shown in INIT.
"""

IS_DUMMY = True


def build_new_path(nr, vlan_id):
    """DEPLOY: your script that creates the L2 path for a new VLAN."""
    return {
        "SW1": {"Gi1/1": "trunk"},
        "SW2": {"Gi1/1": "trunk"},
    }


def find_existing_path(nr, vlan_id):
    """CEASE: your script that finds where the VLAN is today."""
    return {
        "SW1": {"Gi1/1": "trunk"},
        "SW2": {"Gi1/1": "trunk"},
    }
