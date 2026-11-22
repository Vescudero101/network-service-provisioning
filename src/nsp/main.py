"""Entry point.

    python -m nsp.main --service l2_vlan --input examples/l2_vlan_input.yaml --offline
    python -m nsp.main --service l2_vlan --input examples/l2_vlan_input.yaml --dry-run
    python -m nsp.main --service l2_vlan --input examples/l2_vlan_input.yaml
    python -m nsp.main --tui                 (add --offline to try it without devices)

The input file has an "action" (deploy or cease). In the TUI, dry run is a button, chosen for each run.
"""
import argparse
import sys

from nsp.errors import JobError
from nsp.job import create_job
from nsp.run_job import run_job
from nsp.services.registry import SERVICES
from nsp.ui import cli
from nsp.utils.yaml_tools import load_yaml


def parse_args():
    parser = argparse.ArgumentParser(description="Deploy a network service")
    parser.add_argument("--service", choices=list(SERVICES), help="service type")
    parser.add_argument("--input", help="YAML file with the service input")
    parser.add_argument("--dry-run", action="store_true",
                        help="read devices, validate and plan, but push nothing")
    parser.add_argument("--offline", action="store_true",
                        help="no devices at all (implies --dry-run): build data and render config only")
    parser.add_argument("--tui", action="store_true", help="start the Textual interface")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.tui and args.dry_run:
        sys.exit("--dry-run is not used with --tui: the TUI has a Dry run button for each run")
    dry_run = args.dry_run or args.offline

    nr = None
    if not args.offline:
        from nsp.nornir_setup import init_nornir
        nr = init_nornir()

    if args.tui:
        from nsp.ui.tui.app import NspApp      # imported here so Textual stays optional
        NspApp(nr).run()
        return

    if not args.service or not args.input:
        sys.exit("Give --service and --input (or use --tui)")

    user_input = load_yaml(args.input)
    user_input["service_type"] = args.service

    job = create_job(user_input, cli.report, dry_run)
    try:
        run_job(job, nr, cli.ask_confirm)
    except JobError as error:
        print(f"\nSTOPPED: {error}")
        if job.apply_started:
            print(f"Config was already pushed. Rollback is not automatic yet: restore from {job.folder / 'backups'}")
        sys.exit(1)

    print(f"\nDone: {job.status}\nJob folder: {job.folder}")


if __name__ == "__main__":
    main()
