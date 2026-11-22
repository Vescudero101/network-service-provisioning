"""HEALTH CHECK (SKELETON: no checks written yet): general device health after VERIFY.

VERIFY asks "did the service land as intended?". HEALTH CHECK asks "is the device still healthy?"
It does not depend on the service: the same checks run on every device the job touched
(for example: CPU, memory, no new errors in the log, routing neighbours still up).

To add a check, write a function and add it to HEALTH_CHECKS:

    def check_cpu(device_name, nr):
        ...
        return []                      # or a list of problem texts, e.g. ["CPU is 95%"]

Until HEALTH_CHECKS has at least one check, run_job.py shows the phase as skipped (not as a tick),
because a tick on a check that does not exist would mislead. The function arguments may change when
the first real check is written (for example to collect the show commands once per device).
"""
from nsp.errors import HealthCheckFailed

HEALTH_CHECKS = []      # each one: function(device_name, nr) -> list of problem texts


def health_check(job, nr):
    problems = []
    for device_name in job.service_intent["devices"]:
        for check in HEALTH_CHECKS:
            for problem in check(device_name, nr):
                problems.append(f"{device_name}: {problem}")

    if problems:
        raise HealthCheckFailed("\n".join(problems))
    job.report("HEALTH_CHECK", f"{len(HEALTH_CHECKS)} health check(s) passed on every device")
