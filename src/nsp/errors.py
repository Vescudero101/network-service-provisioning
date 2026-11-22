"""Our own error types, so each UI (CLI or TUI) can decide how to show them.
All of them inherit from JobError, so a UI can catch just that one."""


class JobError(Exception):
    """Base class: anything that stops a job in a way we expect."""


class InputError(JobError):
    """The user input or the service intent is wrong or incomplete."""


class ValidationFailed(JobError):
    """A pre-check says the change is not safe. Nothing was touched."""


class JobCancelled(JobError):
    """The user said no at the confirm step."""


class DeviceError(JobError):
    """A device could not be reached or a command failed."""


class ApplyFailed(JobError):
    """Config was pushed but the result is not what we expected."""


class HealthCheckFailed(JobError):
    """A general device health check failed after the change was pushed."""
