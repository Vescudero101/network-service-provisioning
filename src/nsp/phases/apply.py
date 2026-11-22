"""APPLY: push the config, one section at a time (add / remove, in the service's order),
and check the result after each section."""
from nsp.errors import ApplyFailed, DeviceError
from nsp.features.registry import features_on_device, get_feature
from nsp.phases.verify import check_results
from nsp.tasks.push import push_config_task
from nsp.utils.yaml_tools import save_json


def refuse_features_without_checks(job):
    """Never push config for a feature whose pre/post checks are not written yet."""
    for device_data in job.service_intent["devices"].values():
        for feature_name in features_on_device(device_data):
            if not get_feature(feature_name).IMPLEMENTED:
                raise ApplyFailed(
                    f"Feature '{feature_name}' has no checks yet (IMPLEMENTED = False). "
                    "Write its parse_output/validate/check_result first."
                )


def apply_config(job, nr):
    refuse_features_without_checks(job)
    push_log = {}

    for section in job.section_order:
        lines_by_device = {
            device: sections[section] for device, sections in job.plan.items() if sections[section]
        }
        if not lines_by_device:
            continue

        job.report("APPLY", f"Section '{section}' on {', '.join(lines_by_device)}")
        selected = nr.filter(filter_func=lambda host: host.name in lines_by_device)
        results = selected.run(task=push_config_task, lines_by_device=lines_by_device)
        for device in lines_by_device:
            if results[device].failed:
                raise DeviceError(f"{device}: push failed: {results[device].exception}")
        push_log[section] = lines_by_device

        # Check this section before starting the next one (for example: new trunk works before removing the old)
        problems = check_results(job, nr, section, f"postchecks_{section}", "APPLY")
        if problems:
            # TODO: apply-until-converged: re-send only what is missing, up to settings.RETRY_ATTEMPTS
            raise ApplyFailed("\n".join(problems))
        job.report("APPLY", f"Section '{section}' pushed and checked OK")

    save_json(job.folder / "results.json", push_log)
