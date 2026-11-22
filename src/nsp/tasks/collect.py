"""Run all the show commands for one device in ONE session."""
from nornir.core.task import Result, Task
from nornir_scrapli.tasks import send_commands


def collect_task(task: Task, commands_by_device: dict) -> Result:
    commands = commands_by_device[task.host.name]
    response = task.run(task=send_commands, commands=commands)

    outputs = {}
    # NOTE: check this against your nornir-scrapli version (test on one device first)
    for item in response[0].scrapli_response:
        outputs[item.channel_input] = item.result
    return Result(host=task.host, result=outputs)
