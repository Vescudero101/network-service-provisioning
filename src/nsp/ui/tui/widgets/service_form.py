"""A form drawn from a list of fields (see ACTIONS in services/l2_vlan.py). One form per service action."""
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Input, Label, Select

from nsp.errors import InputError


class ServiceForm(VerticalScroll):
    def __init__(self, fields, **kwargs):
        super().__init__(**kwargs)
        self.fields = fields

    def compose(self):
        for field in self.fields:
            suffix = "" if field.get("required", True) else " (optional)"
            label = field["label"] + suffix
            widget_id = f"field-{field['name']}"

            if field["kind"] == "select":
                options = field["options"]
                widget = Select([(option, option) for option in options],
                                value=options[0], allow_blank=False, id=widget_id, compact=True)
            else:
                widget = Input(placeholder=field.get("placeholder", ""), id=widget_id, compact=True)

            with Horizontal(classes="form-row"):
                yield Label(label, classes="form-label")
                yield widget

    def get_values(self):
        """Returns the dictionary the service expects, or raises InputError."""
        values = {}
        for field in self.fields:
            widget = self.query_one(f"#field-{field['name']}")
            kind = field["kind"]

            if kind == "select":
                value = widget.value
            else:
                value = widget.value.strip()
                if kind == "int" and value:
                    if not value.isdigit():
                        raise InputError(f"'{field['label']}' must be a number")
                    value = int(value)

            if value in ("", None):
                if field.get("required", True):
                    raise InputError(f"'{field['label']}' is required")
                continue
            values[field["name"]] = value
        return values
