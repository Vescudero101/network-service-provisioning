"""VERIFY: collect the live state again and compare it with what we wanted."""
from nsp.errors import ApplyFailed
from nsp.features.registry import features_on_device, get_feature
from nsp.phases.discover import collect_live_state


def check_results(job, nr, section, folder_name, phase):
    """section = "add", "remove" or None (check everything). Returns a list of problems."""
    live_state = collect_live_state(job, nr, folder_name, phase)
    problems = []
    for device_name, device_data in job.resolved_intent["devices"].items():
        for feature_name in features_on_device(device_data):
            feature = get_feature(feature_name)
            if not feature.IMPLEMENTED:
                continue
            items = device_data[feature_name]
            if section is not None:
                to_add, to_remove = feature.split_by_action(items)
                items = to_add if section == "add" else to_remove
            if not items:
                continue
            live = live_state[device_name][feature_name]
            for problem in feature.check_result(items, live):
                problems.append(f"{device_name}: {problem}")
    return problems


def verify(job, nr):
    problems = check_results(job, nr, None, "postchecks", "VERIFY")
    if problems:
        raise ApplyFailed("\n".join(problems))
    job.report("VERIFY", "All checks passed")
