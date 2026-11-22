"""Get the full running config of one device."""
from nornir.core.task import Result, Task
from nornir_scrapli.tasks import send_command


def backup_task(task: Task) -> Result:
    response = task.run(task=send_command, command="show running-config")
    return Result(host=task.host, result=response.result)
