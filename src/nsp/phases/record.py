"""RECORD: always runs, even when the job failed. Writes audit.json in the job folder."""
from datetime import datetime

from nsp.utils.yaml_tools import save_json


def record(job):
    audit = {
        "operator": job.operator,
        "started_at": job.started_at,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "status": job.status,
        "dry_run": job.dry_run,
        "service": job.service_intent.get("service"),
        "problems": job.problems,
        "plan": job.plan,
    }
    save_json(job.folder / "audit.json", audit)
    # TODO (optional): copy audit.json to the audit repo and push (after redacting secrets)
