"""Put your existing NetBox -> Nornir script here.

init_nornir() must return the Nornir object (nr). main.py calls it once and passes nr to run_job.
"""


def init_nornir():
    raise NotImplementedError(
        "Paste your NetBox inventory script into nsp/nornir_setup/__init__.py "
        "and return the nr object. Use --offline to try the tool without devices."
    )
