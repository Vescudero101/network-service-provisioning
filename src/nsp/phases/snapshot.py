"""SNAPSHOT: save the full config of every device before changing anything.
Backups are saved as-is (rollback needs the secrets) with owner-only permissions."""
from nsp.errors import DeviceError
from nsp.tasks.backup import backup_task
from nsp.utils.yaml_tools import save_text


def snapshot(job, nr):
    if job.dry_run or nr is None:
        job.report("SNAPSHOT", "Skipped (dry run)")
        return

    devices = job.service_intent["devices"]
    selected = nr.filter(filter_func=lambda host: host.name in devices)
    results = selected.run(task=backup_task)

    folder = job.folder / "backups"
    folder.mkdir(exist_ok=True)
    for name in devices:
        if name not in results or results[name].failed:
            raise DeviceError(f"{name}: backup failed")
        save_text(folder / f"{name}.cfg", results[name][0].result, private=True)
        job.report("SNAPSHOT", f"{name}: config saved")
