"""
Like minutes.io, but in the terminal.
"""

from dataclasses import dataclass, field
from itertools import count
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container, Grid
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (Button, Footer, Header, Static, Input, ListItem, MarkdownViewer)

from xdg.BaseDirectory import save_data_path


class Minute(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    attendees: str
    about: Optional[str] = None


def init_database():
    db_path = save_data_path("minutes") + "minutes.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)

    return engine


engine = init_database()


def minutes_all():
    with Session(engine) as session:
        statement = select(Minute)
        return [minute for minute in session.exec(statement)]


def minute_save(minute: Minute):
    with Session(engine) as session:
        session.add(minute)
        session.commit()
        session.refresh(minute)


def minute_get(minute_id):
    if not minute_id:
        return None

    with Session(engine) as session:
        minute = session.exec(
            select(Minute).where(Minute.id == minute_id)
        ).first()

        return minute


def minute_delete(minute):
    with Session(engine) as session:
        session.delete(minute)
        session.commit()


class MinuteListItem(Widget):
    def __init__(self, minute):
        super().__init__()
        self.minute = minute

    def compose(self) -> ComposeResult:
        item_text = f"[b]{self.minute.title}[/b] [@click=minute_view({self.minute.id})]:mag:[/] [@click=minute_edit({self.minute.id})]:pencil:[/] [@click=minute_delete({self.minute.id})]:wastebasket:[/]"

        yield ListItem(Static(item_text))


class MinutesList(Widget):
    def compose(self) -> ComposeResult:
        minutes = minutes_all()

        yield Vertical(
            *(MinuteListItem(minute) for minute in minutes),
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
        self.app.push_screen(MinuteEditScreen(minute_id=None))


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

    def __init__(self, minute_id=None):
        super().__init__()
        self.minute = minute_get(minute_id)

    def compose(self) -> ComposeResult:
        title = self.minute.title if self.minute else ""
        attendees = self.minute.attendees if self.minute else ""
        about = self.minute.about if self.minute else ""

        yield Header()
        yield Static("", id="left-sidebar")
        with Container(id="minute-meta"):
            yield Input(value=title, placeholder="title", id="title")
            yield Input(value=attendees, placeholder="attendees", id="attendees")
            yield Input(value=about, placeholder="about", id="about")
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

        minute = Minute(title=title, attendees=attendees, about=about)
        minute_save(minute)

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


class MinuteViewScreen(Screen):

    BINDINGS = [
        ("t", "toggle_table_of_contents", "TOC"),
        ("b", "back", "Back"),
        ("f", "forward", "Forward"),
    ]

    def __init__(self, minute_id):
        super().__init__()
        self.minute_id = minute_id

    def compose(self) -> ComposeResult:
        minute = minute_get(self.minute_id)

        MARKDOWN = f"""
# {minute.title}
### Attendees: {minute.attendees}
## About: {minute.about}
"""
        yield Header()
        yield MarkdownViewer(markdown=MARKDOWN, show_table_of_contents=True)
        yield Footer()


class MinuteDeleteScreen(Screen):

    def __init__(self, minute_id):
        super().__init__()
        self.minute_id = minute_id

    def compose(self) -> ComposeResult:
        yield Grid(
            Static("Are you sure you want to delete?", id="question"),
            Button("No", variant="error", id="no"),
            Button("Yes!", variant="primary", id="yes"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            minute = minute_get(self.minute_id)
            minute_delete(minute)
            self.app.push_screen(MinutesScreen())
        else:
            self.app.pop_screen()


class MinutesApp(App):
    """Textual minutes app."""

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]
    CSS_PATH = "minutes.css"
    SCREENS = {
        "minutes_list": MinutesScreen(),
        "minute_edit": MinuteEditScreen(),
        "minute_view": MinuteViewScreen(minute_id=None),
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
    def action_minute_view(self, minute_id) -> None:
        self.push_screen(MinuteViewScreen(minute_id))

    def action_minute_edit(self, minute_id) -> None:
        self.push_screen(MinuteEditScreen(minute_id))

    def action_minute_delete(self, minute_id) -> None:
        self.push_screen(MinuteDeleteScreen(minute_id))


def run():
    MinutesApp().run()
