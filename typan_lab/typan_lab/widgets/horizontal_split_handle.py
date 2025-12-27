from __future__ import annotations

from dataclasses import dataclass

from rich.text import Text
from textual.events import Enter, Leave, MouseDown, MouseMove, MouseUp
from textual.message import Message
from textual.widget import Widget


class HorizontalSplitHandle(Widget):
    @dataclass
    class SplitDragged(Message):
        # nowa pozycja splitu liczona jako "Y na ekranie"
        screen_y: int

        @property
        def bubble(self) -> bool:
            return True

    def __init__(self, *, id: str | None = None) -> None:
        super().__init__(id=id)
        self._dragging = False
        self._hovered = False

    def render(self) -> Text:
        in_use = self._dragging or self._hovered
        if in_use:
            return Text("↑\n↓", justify="center", style="bold")
        return Text("⇅", justify="center", style="bold")

    def on_enter(self, event: Enter) -> None:
        self._hovered = True
        self.add_class("-hover")

    def on_leave(self, event: Leave) -> None:
        self._hovered = False
        if not self._dragging:
            self.remove_class("-hover")

    def on_mouse_down(self, event: MouseDown) -> None:
        self._dragging = True
        self.capture_mouse()
        self.remove_class("-hover")
        self.add_class("-dragging")
        self.refresh()
        event.stop()

    def on_mouse_up(self, event: MouseUp) -> None:
        if not self._dragging:
            return
        self._dragging = False
        self.release_mouse()
        self.remove_class("-dragging")
        self.add_class("-hover")
        self.refresh()
        event.stop()

    def on_mouse_move(self, event: MouseMove) -> None:
        if not self._dragging:
            return
        self.post_message(self.SplitDragged(event.screen_y))
        event.stop()
