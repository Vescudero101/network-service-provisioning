"""VALIDATE: intent vs live state. Decides if it is safe to continue. Read-only."""
from nsp.errors import ValidationFailed
from nsp.features.registry import features_on_device, get_feature
from nsp.utils.yaml_tools import save_json


def validate(job):
    problems = []
    for device_name, device_data in job.service_intent["devices"].items():
        for feature_name in features_on_device(device_data):
            feature = get_feature(feature_name)
            if not feature.IMPLEMENTED:
                job.report("VALIDATE", f"WARNING {device_name}: no checks written yet for '{feature_name}'")
                continue
            live = job.live_state[device_name][feature_name]
            found = feature.validate(device_data[feature_name], live, device_data)
            for problem in found:
                problems.append(f"{device_name}: {problem}")
            if not found:
                job.report("VALIDATE", f"OK  {device_name}: {feature_name}")

    job.problems = problems
    save_json(job.folder / "validation.json", {"ok": not problems, "problems": problems})
    if problems:
        raise ValidationFailed("\n".join(problems))
