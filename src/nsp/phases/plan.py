"""PLAN: fill in values that depend on the device (resolve), then render the config.
Output: resolved_intent.yaml and job.plan = {device: {"add": [lines], "remove": [lines]}}"""
import copy

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from nsp import settings
from nsp.errors import InputError
from nsp.features.registry import features_on_device, get_feature
from nsp.phases.summary import plan_text
from nsp.utils.yaml_tools import save_text, save_yaml


def platform_for(device_name, nr):
    if nr is None:
        return settings.DEFAULT_PLATFORM
    return nr.inventory.hosts[device_name].platform or settings.DEFAULT_PLATFORM


def render_feature(environment, platform, feature_name, items):
    try:
        template = environment.get_template(f"{platform}/{feature_name}.j2")
    except TemplateNotFound:
        raise InputError(f"No template: templates/{platform}/{feature_name}.j2")
    text = template.render(items=items)
    return [line for line in text.splitlines() if line.strip()]


def plan(job, nr):
    environment = Environment(
        loader=FileSystemLoader(str(settings.TEMPLATES_DIR)),
        trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True,
    )
    resolved = copy.deepcopy(job.service_intent)
    job.plan = {}
    (job.folder / "rendered_config").mkdir(exist_ok=True)

    for device_name, device_data in resolved["devices"].items():
        platform = platform_for(device_name, nr)
        feature_names = features_on_device(device_data)

        # 1. resolve live-dependent values, then split every feature into add / remove
        splits = {}
        for feature_name in feature_names:
            feature = get_feature(feature_name)
            resolve = getattr(feature, "resolve", None)             # optional hook
            if feature.IMPLEMENTED and resolve:
                live = job.live_state[device_name][feature_name]
                device_data[feature_name] = resolve(device_data[feature_name], live)
            splits[feature_name] = feature.split_by_action(device_data[feature_name])

        # 2. add in feature order, remove in the opposite order
        add_lines = []
        for feature_name in feature_names:
            to_add, _ = splits[feature_name]
            if to_add:
                add_lines += render_feature(environment, platform, feature_name, to_add)

        remove_lines = []
        for feature_name in reversed(feature_names):
            _, to_remove = splits[feature_name]
            if to_remove:
                remove_lines += render_feature(environment, platform, feature_name, to_remove)

        job.plan[device_name] = {"add": add_lines, "remove": remove_lines}

        text = "! --- ADD ---\n" + "\n".join(add_lines) + "\n! --- REMOVE ---\n" + "\n".join(remove_lines) + "\n"
        save_text(job.folder / "rendered_config" / f"{device_name}.txt", text)

    job.resolved_intent = resolved
    save_yaml(job.folder / "resolved_intent.yaml", resolved)

    job.report("PLAN", plan_text(job) if has_changes(job) else "Nothing to change: the devices already match")


def has_changes(job):
    return any(lines for sections in job.plan.values() for lines in sections.values())
