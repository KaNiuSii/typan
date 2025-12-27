from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import TextArea

class TerminalPanel(Widget):
    def compose(self) -> ComposeResult:
        term = TextArea("", read_only=True, id="terminal")
        term.load_text("Terminal panel (placeholder)\n> Later: wire to PTY / subprocess\n")
        yield term

    def write(self, text: str) -> None:
        term = self.query_one("#terminal", TextArea)
        term.insert(text)
