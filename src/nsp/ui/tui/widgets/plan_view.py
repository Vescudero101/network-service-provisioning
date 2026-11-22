"""The PLAN output: a table with one row per device. Enter on a row opens that device's config.

Works for 1 or for 20 devices: the table stays short, the config is one keypress away
(the screen opens screens/config.py full screen, Esc comes back).
"""
from textual.containers import Vertical
from textual.widgets import DataTable, Static

from nsp.phases.summary import table_rows


class PlanView(Vertical):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plan_info = {}

    def compose(self):
        yield Static("Up/Down to choose a device, Enter to read the config that will be pushed to it",
                     classes="plan-hint")
        yield DataTable(id="plan-table", cursor_type="row", zebra_stripes=True)

    def on_mount(self):
        self.query_one(DataTable).add_columns("Device", "Add", "Remove", "Items")

    def show(self, plan_info):
        """plan_info = summarise_plan(job)"""
        self.plan_info = plan_info
        table = self.query_one(DataTable)
        table.clear()
        for device_name, added, removed, items in table_rows(plan_info):
            table.add_row(device_name, added, removed, items, key=device_name)

    def clear(self):
        self.plan_info = {}
        self.query_one(DataTable).clear()

    def focus_table(self):
        self.query_one(DataTable).focus()

    def config_of(self, device_name):
        return self.plan_info[device_name]["config"]
