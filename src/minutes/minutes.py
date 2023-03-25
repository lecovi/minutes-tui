"""
Like minutes.io, but in the terminal.
"""

from dataclasses import dataclass, field
from itertools import count

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Static, Input, ListItem:x


@dataclass
class Minute:
    """Class for keeping track of an item in inventory."""

    id: int = field(default_factory=lambda counter=count(): next(counter), init=False)
    title: str
    attendees: str
    about: str


_minutes = []


class MinuteListItem(Widget):
    def __init__(self, item):
        super().__init__()
        self.item = item

    def compose(self) -> ComposeResult:
        item_text = f"[b]{self.item.title}[/b] [@click=view_item()]:mag:[/] [@click=edit_item()]:pencil:[/] [@click=delete_item()]:wastebasket:[/]"

        yield ListItem(Static(item_text))


class MinutesList(Widget):
    def compose(self) -> ComposeResult:
        yield Vertical(
            *(MinuteListItem(minute) for minute in _minutes),
            id="minutes-screen-content",
        )


class MinutesScreen(Screen):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("n", "new_minute", "New Minute"),
        ("j", "next_minute", "Next minute"),
        ("k", "previous_minute", "Previous minute"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="left-sidebar")
        with Vertical(id="minutes-screen-content-wrapper"):
            yield Button("New!", id="new-minute-button", variant="success")
            yield MinutesList(id="minutes-list")
        yield Static("", id="right-sidebar")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.push_screen(MinuteEditScreen())


class MinuteBullet(Widget):
    def compose(self) -> None:
        yield Horizontal(
            Input(placeholder="bullet", id="bullet")
        )


class MinuteEditScreen(Screen):

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "add_bullet", "Add bullet"),
        ("r", "remove_bullet", "Remove bullet"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="left-sidebar")
        with Container(id="minute-meta"):
            yield Input(placeholder="title", id="title")
            yield Input(placeholder="attendees", id="attendees")
            yield Input(placeholder="about", id="about")
        yield Container(id="bullets")
        with Horizontal(id="buttons"):
            yield Button("Cancel", name="cancel", variant="error")
            yield Button("Save", name="save", variant="primary")
        yield Static("", id="right-sidebar")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.name == "save":
            self.create_minute()
        self.app.push_screen(MinutesScreen())

    def create_minute(self) -> None:
        title = self.query_one("#title", Input).value
        attendees = self.query_one("#attendees", Input).value
        about = self.query_one("#about", Input).value

        minute = Minute(title, attendees, about)

        _minutes.append(minute)

    def action_add_bullet(self) -> None:
        """An action to add new bullet to minute."""
        bullet = MinuteBullet()
        self.query_one("#bullets").mount(bullet)
        bullet.scroll_visible()

    def action_remove_bullet(self) -> None:
        """An action to remove previous bullet."""
        bullets = self.query("MinuteBullet")
        if bullets:
            bullets.last().remove()


class MinutesApp(App):
    """Textual minutes app."""

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]
    CSS_PATH = "minutes.css"
    SCREENS = {
        "minutes_list": MinutesScreen(),
        "minute_edit": MinuteEditScreen(),
    }

    def on_mount(self) -> None:
        """Set up the application on startup."""
        self.push_screen("minutes_list")

    def action_new_minute(self) -> None:
        """An action to create a new minute."""
        self.app.push_screen(MinuteEditScreen())

    def action_next_minute(self) -> None:
        """An action to focus next minute."""
        self.query_one("#minutes-list", MinutesList).focus_next()

    def action_previous_minute(self) -> None:
        """An action to focus previous minute."""
        self.query_one("#minutes-list", MinutesList).focus_previous()


def run():
    MinutesApp().run()
