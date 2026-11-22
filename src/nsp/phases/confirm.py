"""CONFIRM: the plan was already shown by the PLAN phase. Ask. The UI decides how to ask."""
from nsp.errors import JobCancelled


def confirm(job, ask_confirm):
    if not ask_confirm():
        raise JobCancelled("Cancelled at the confirm step. Nothing was pushed.")
