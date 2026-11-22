"""Main menu: services on the left, what you need to know on the right."""
from pathlib import Path

from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, Markdown

from nsp.services.registry import SERVICES
from nsp.ui.tui.screens.deploy import DeployScreen

INFO_DIR = Path(__file__).resolve().parents[1] / "info"      # plain Markdown files you can edit


def read_info(name):
    path = INFO_DIR / f"{name}.md"
    return path.read_text() if path.exists() else ""


class MainMenuScreen(Screen):
    BINDINGS = [("q", "app.quit", "Quit")]

    def compose(self):
        yield Header()
        with Horizontal(id="menu-body"):
            with Vertical(id="menu-panel"):
                yield Label("SERVICES", classes="panel-title")
                items = [ListItem(Label(service.TITLE), name=key) for key, service in SERVICES.items()]
                items.append(ListItem(Label("Quit"), name="quit"))
                yield ListView(*items, id="service-list")
            with VerticalScroll(id="info-panel"):
                yield Markdown(id="info")
        yield Footer()

    def on_mount(self):
        self.query_one("#service-list", ListView).focus()
        self.show_info(next(iter(SERVICES)))

    def show_info(self, key):
        text = read_info("general")
        if key in SERVICES:
            text += "\n\n---\n\n" + read_info(key)
        self.query_one("#info", Markdown).update(text)

    def on_list_view_highlighted(self, event):
        if event.item is not None:
            self.show_info(event.item.name)

    async def on_list_view_selected(self, event):
        if event.item.name == "quit":
            await self.app.action_quit()
        else:
            self.app.push_screen(DeployScreen(event.item.name))
