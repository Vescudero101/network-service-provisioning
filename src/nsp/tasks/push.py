"""Push config lines to one device. A device error message counts as a failure."""
from nornir.core.task import Result, Task
from nornir_scrapli.tasks import send_configs

from nsp import settings


def push_config_task(task: Task, lines_by_device: dict) -> Result:
    lines = lines_by_device[task.host.name]
    response = task.run(
        task=send_configs,
        configs=lines,
        failed_when_contains=settings.ERROR_MARKERS,
        stop_on_failed=True,
    )
    return Result(host=task.host, result=response.result)
