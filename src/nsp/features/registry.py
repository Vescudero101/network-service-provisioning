"""The list of features, and the order they are applied in."""
from nsp.errors import InputError
from nsp.features import bgp, interfaces, vlans, vrfs

FEATURES = {
    "vrfs": vrfs,
    "vlans": vlans,
    "interfaces": interfaces,
    "bgp": bgp,
}

# Order used when ADDING. When removing, the runner goes in the opposite order.
FEATURE_ORDER = ["vrfs", "vlans", "interfaces", "bgp"]


def get_feature(name):
    if name not in FEATURES:
        raise InputError(f"Unknown feature '{name}'. Known features: {', '.join(FEATURES)}")
    return FEATURES[name]


def features_on_device(device_data):
    """Names of the features used on one device, in the 'add' order."""
    for name in device_data:
        get_feature(name)                       # stops with a clear message on a typo
    return [name for name in FEATURE_ORDER if name in device_data]
