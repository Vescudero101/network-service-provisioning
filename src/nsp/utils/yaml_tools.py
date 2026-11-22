"""Small helpers to read and write files."""
import json
import os
from pathlib import Path

import yaml

from nsp.errors import InputError


def load_yaml(path):
    with open(path) as file:
        return yaml.safe_load(file)


def save_yaml(path, data):
    with open(path, "w") as file:
        yaml.safe_dump(data, file, sort_keys=False)


def save_json(path, data):
    with open(path, "w") as file:
        json.dump(data, file, indent=2, default=str)


def save_text(path, text, private=False):
    Path(path).write_text(text)
    if private:
        os.chmod(path, 0o600)       # only the owner can read (used for backups)


def check_required_keys(data, required_keys):
    missing = [key for key in required_keys if key not in data]
    if missing:
        raise InputError(f"Missing input fields: {', '.join(missing)}")
