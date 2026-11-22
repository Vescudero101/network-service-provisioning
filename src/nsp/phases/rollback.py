"""ROLLBACK (SKELETON): automatic restore is not written yet.
The backups are in jobs/<job>/backups/. Restore manually until tasks/rollback.py is tested on a lab switch."""


def rollback(job, nr):
    job.report("ROLLBACK", f"NOT automatic yet. Restore manually from: {job.folder / 'backups'}")
