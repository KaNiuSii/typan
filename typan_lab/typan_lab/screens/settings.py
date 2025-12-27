from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Label, Select, Static

class SettingsScreen(Screen):
    BINDINGS = [("escape", "close", "Back")]

    def compose(self) -> ComposeResult:
        s = self.app.state.settings  # type: ignore

        with Vertical(id="settings-root"):
            yield Static("Settings", id="settings-title")

            with Horizontal():
                yield Label("Indent style:")
                yield Select(
                    [("Spaces", "spaces"), ("Tabs", "tabs")],
                    value=s.indent_style,
                    id="indent_style",
                )

            with Horizontal():
                yield Label("Indent size:")
                yield Select(
                    [("2", "2"), ("4", "4"), ("8", "8")],
                    value=str(s.indent_size),
                    id="indent_size",
                )

            with Horizontal():
                yield Label("Format on:")
                yield Select(
                    [("Off", "off"), ("On Save", "on_save"), ("On Update", "on_update")],
                    value=s.format_mode,
                    id="format_mode",
                )

            with Horizontal(id="settings-actions"):
                yield Button("Close", id="close")
                yield Button("Apply", id="apply", variant="primary")

    def action_close(self) -> None:
        self.app.pop_screen()  # type: ignore

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.action_close()
        elif event.button.id == "apply":
            self._apply()

    def _apply(self) -> None:
        app = self.app  # type: ignore
        indent_style = self.query_one("#indent_style", Select).value
        indent_size = int(self.query_one("#indent_size", Select).value)
        format_mode = self.query_one("#format_mode", Select).value

        app.state.settings.format_mode = format_mode # type: ignore
        app.state.settings.indent_style = indent_style  # type: ignore
        app.state.settings.indent_size = indent_size  # type: ignore

        app.apply_settings()
        app.save_settings()

        self.notify("Settings applied")
        self.action_close()
