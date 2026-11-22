"""INIT: check the user input, create service_intent.yaml (the contract for all later phases).

The user first picks an action (deploy or cease) and then fills the form of that action.
Each service lists its actions in ACTIONS (see services/l2_vlan.py): the form fields and the function
that builds the service intent. INIT may call your scripts (path discovery): they only read.
"""
from nsp import settings
from nsp.errors import InputError
from nsp.features.registry import features_on_device, get_feature
from nsp.services.registry import SERVICES
from nsp.utils.actions import ITEM_ACTION
from nsp.utils.yaml_tools import check_required_keys, save_yaml


def required_field_names(fields):
    return [field["name"] for field in fields if field.get("required", True)]


def initialize(job, nr):
    service_type = job.user_input["service_type"]
    if service_type not in SERVICES:
        raise InputError(f"Unknown service '{service_type}'. Known services: {', '.join(SERVICES)}")
    service = SERVICES[service_type]

    action = job.user_input.get("action")
    if action not in service.ACTIONS:
        raise InputError(f"Unknown action '{action}' for {service.TITLE}. Known actions: {', '.join(service.ACTIONS)}")
    action_settings = service.ACTIONS[action]

    check_required_keys(job.user_input, required_field_names(action_settings["fields"]))
    save_yaml(job.folder / "service_input.yaml", job.user_input)

    if getattr(service, "USES_DUMMY_DATA", False):
        job.report("INIT", f"WARNING: {service.TITLE} is using DUMMY path data (placeholder scripts), not real devices")

    job.section_order = getattr(service, "SECTION_ORDER", settings.SECTION_ORDER)
    service_intent = action_settings["create_service_intent"](job.user_input, nr)
    service_intent["service"]["action"] = action

    # Every item gets an explicit action, so later phases never think about defaults
    default_item_action = ITEM_ACTION[action]
    for device_data in service_intent["devices"].values():
        for feature_name in features_on_device(device_data):
            get_feature(feature_name).fill_actions(device_data[feature_name], default_item_action)

    job.service_intent = service_intent
    save_yaml(job.folder / "service_intent.yaml", service_intent)
    job.report("INIT", f"service_intent.yaml created ({action}) for: {', '.join(service_intent['devices'])}")
