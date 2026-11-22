"""What the PLAN phase shows the user: a table with one row per device, the full config of a device on demand.
Everything here is plain text and dicts, so the CLI and the TUI use the same functions."""
from nsp.features.registry import features_on_device, get_feature


def default_summary(items):
    """One row per item: (action, name, details). Works for any feature whose items are {name: item}."""
    rows = []
    for name, item in items.items():
        details = " ".join(f"{key}={value}" for key, value in item.items() if key != "action")
        rows.append((item["action"], str(name), details))
    return rows


def config_text(job, sections):
    """The config lines of one device, in the order they will be pushed."""
    lines = []
    for section in job.section_order:
        if sections[section]:
            lines.append(f"! --- {section.upper()} ---")
            lines += sections[section]
    return "\n".join(lines)


def summarise_plan(job):
    """{device: {"rows": [(action, feature, name, details)], "added": n, "removed": n, "config": text}}"""
    result = {}
    for device_name, device_data in job.resolved_intent["devices"].items():
        rows = []
        for feature_name in features_on_device(device_data):
            feature = get_feature(feature_name)
            summarise = getattr(feature, "summarise", default_summary)
            for action, name, details in summarise(device_data[feature_name]):
                rows.append((action, feature_name, name, details))

        sections = job.plan[device_name]
        result[device_name] = {
            "rows": rows,
            "added": len(sections["add"]),
            "removed": len(sections["remove"]),
            "config": config_text(job, sections),
        }
    return result


def items_text(rows):
    """Short text for the table: 'vlans: +200  interfaces: +Gi1/1, -Gi0/5'"""
    names_by_feature = {}
    for action, feature, name, details in rows:
        sign = "+" if action == "add" else "-"
        names_by_feature.setdefault(feature, []).append(f"{sign}{name}")
    return "  ".join(f"{feature}: {', '.join(names)}" for feature, names in names_by_feature.items())


def table_rows(plan_info):
    """One row per device for the plan table: [(device, lines added, lines removed, items text)]."""
    return [
        (device_name, info["added"], info["removed"], items_text(info["rows"]))
        for device_name, info in plan_info.items()
    ]


def summary_lines(device_name, info):
    total = info["added"] + info["removed"]
    lines = [f"{device_name}   {total} config lines ({info['added']} add, {info['removed']} remove)"]
    for action, feature, name, details in info["rows"]:
        lines.append(f"   {action.upper():<7} {feature:<11} {name}  {details}")
    return lines


def plan_text(job):
    """Everything as text, for the CLI and for the log."""
    lines = []
    for device_name, info in summarise_plan(job).items():
        lines += summary_lines(device_name, info)
        lines.append("")
        lines += [f"   {line}" for line in info["config"].splitlines()]
        lines.append("")
    return "\n".join(lines).strip()
