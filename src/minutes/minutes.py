"""
Like minutes.io, but in the terminal.
"""

from dataclasses import dataclass, field
from itertools import count
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Static, Input

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


class MinuteListItem(Widget):
    def __init__(self, item):
        super().__init__()
        self.item = item

    def compose(self) -> ComposeResult:
        item_text = f"[b]{self.item.title}[/b] [@click=view_item()]:mag:[/] [@click=edit_item()]:pencil:[/] [@click=delete_item()]:wastebasket:[/]"

        yield Static(item_text)


class MinutesList(Widget):
    def compose(self) -> ComposeResult:
        minutes = minutes_all()

        yield Vertical(
            *(MinuteListItem(minute) for minute in minutes),
            id="minutes-screen-content",
        )


class MinutesScreen(Screen):

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Static("", id="foo"),
            Vertical(
                Button("New!", id="new-minute", variant="success"),
                MinutesList(id="minutes-list"),
                id="minutes-screen-content-wrapper",
            ),
            Static("", id="baz"),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.push_screen(MinuteEditScreen())


class MinuteEditScreen(Screen):

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Static("", id="foo"),
            Vertical(
                Input(placeholder="title", id="title"),
                Input(placeholder="attendees", id="attendees"),
                Input(placeholder="about", id="about"),
                Horizontal(
                    Button("Cancel", name="cancel", variant="error"),
                    Button("Save", name="save", variant="primary"),
                ),
            ),
            Static("", id="baz"),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.name == "save":
            minute = Minute(
                title=self.query_one("#title", Input).value,
                attendees=self.query_one("#title", Input).value,
                about=self.query_one("#title", Input).value,
            )
            minute_save(minute)

        self.app.push_screen(MinutesScreen())


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


def run():
    MinutesApp().run()
