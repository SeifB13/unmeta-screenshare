from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown

from ..i18n import t


class HelpScreen(Screen[None]):
    BINDINGS = [Binding("escape,q,question_mark", "app.pop_screen", t("key.back"))]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(classes="page"):
            yield Markdown(t("help.body"))
        yield Footer()
