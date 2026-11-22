"""Paths and settings in one place. No other file should hard-code a path."""
import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent          # src/nsp
REPO_ROOT = PACKAGE_DIR.parents[1]                      # the repo root

# Where job folders are created. On the bastion you can point this somewhere shared:
#   export NSP_JOBS_DIR=/var/lib/nsp/jobs
JOBS_DIR = Path(os.environ.get("NSP_JOBS_DIR", REPO_ROOT / "jobs"))
TEMPLATES_DIR = PACKAGE_DIR / "templates"

# Template folder used when a device has no platform in the Nornir inventory.
# The folder name must match the platform names coming from NetBox / your inventory script.
DEFAULT_PLATFORM = "cisco_iosxe"

# Default order of the work. "add" first then "remove" = make-before-break.
# A service can override it (see SECTION_ORDER in services/l2_vlan.py).
SECTION_ORDER = ["add", "remove"]


# If any of these appear in the device output while pushing config, the push counts as failed
ERROR_MARKERS = ["% Invalid", "% Incomplete", "% Ambiguous", "% Access denied"]
