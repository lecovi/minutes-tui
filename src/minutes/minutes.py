"""
Like minutes.io, but in the terminal.

Run with:
    python minutes.py
"""

from textual.app import App, ComposeResult
from textual.containers import Container


class Minutes(App):
    """Textual minutes app."""

    CSS_PATH = "minutes.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Container()


def run():
    Minutes().run()


if __name__ == "__main__":
    run()
