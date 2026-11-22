"""DISCOVER: read the live state of every device, ONE session per device. Read-only."""
from nsp.errors import DeviceError
from nsp.features.registry import features_on_device, get_feature
from nsp.tasks.collect import collect_task
from nsp.utils.yaml_tools import save_json


def build_commands(device_data):
    """All show commands needed by the features used on this device (no duplicates)."""
    commands = []
    for feature_name in features_on_device(device_data):
        commands += get_feature(feature_name).commands_to_collect(device_data[feature_name])
    return list(dict.fromkeys(commands))


def collect_live_state(job, nr, folder_name, phase="DISCOVER"):
    """Used for the pre-checks ('prechecks') and again for the post-checks ('postchecks').
    Returns {device: {feature: parsed live data}}. Raw output is saved in the job folder."""
    devices = job.service_intent["devices"]
    commands_by_device = {name: build_commands(data) for name, data in devices.items()}

    if nr is None:
        job.report(phase, "OFFLINE: no devices, live state is empty (validation is only a demo)")
        raw_outputs = {name: {} for name in devices}
    else:
        selected = nr.filter(filter_func=lambda host: host.name in commands_by_device)
        results = selected.run(task=collect_task, commands_by_device=commands_by_device)
        raw_outputs = {}
        for name in devices:
            if name not in results:
                raise DeviceError(f"{name} is not in the Nornir inventory")
            if results[name].failed:
                raise DeviceError(f"{name}: {results[name].exception}")
            raw_outputs[name] = results[name][0].result

    folder = job.folder / folder_name
    folder.mkdir(exist_ok=True)
    live_state = {}
    for name, device_data in devices.items():
        save_json(folder / f"{name}.json", raw_outputs[name])
        live_state[name] = {
            feature_name: get_feature(feature_name).parse_output(raw_outputs[name])
            for feature_name in features_on_device(device_data)
        }
        job.report(phase, f"{name}: collected {len(commands_by_device[name])} command(s)")
    return live_state


def discover(job, nr):
    job.live_state = collect_live_state(job, nr, "prechecks")
