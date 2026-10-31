from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Markdown

from ..i18n import t


class HelpScreen(Screen[None]):
    BINDINGS = [
        Binding("escape,q,question_mark", "app.pop_screen", t("key.back")),
        Binding("i", "app.copy_diagnostic", t("key.diagnostic")),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(classes="page"):
            with Horizontal(classes="buttons"):
                yield Button(t("help.diagnostic"), id="diagnostic", variant="primary")
            yield Markdown(t("help.body"))
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "diagnostic":
            self.app.run_action("app.copy_diagnostic")
