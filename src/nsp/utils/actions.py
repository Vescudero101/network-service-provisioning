"""Helpers for items that carry an "action" (add or remove)."""
from nsp.errors import InputError

VALID_ACTIONS = ("add", "remove")

# What the user picks at the start (deploy / cease) -> the default action of every item
ITEM_ACTION = {"deploy": "add", "cease": "remove"}


def fill_item_actions(items, default_action):
    """Every item gets an explicit action, always the last key (easier to read in the YAML)."""
    for name, item in items.items():
        action = item.pop("action", default_action)     # take it out (or use the default)
        if action not in VALID_ACTIONS:
            raise InputError(f"'{name}': action must be add or remove, not '{action}'")
        item["action"] = action                         # put it back at the end


def split_items(items):
    """Split a dict of items into (to_add, to_remove)."""
    to_add = {name: item for name, item in items.items() if item["action"] == "add"}
    to_remove = {name: item for name, item in items.items() if item["action"] == "remove"}
    return to_add, to_remove
