from __future__ import annotations

from dataclasses import dataclass

from textual.message import Message
from textual.widget import Widget
from textual.events import MouseDown, MouseMove, MouseUp, Enter, Leave
from rich.text import Text


class VerticalSplitHandle(Widget):
    @dataclass
    class SplitDragged(Message):
        new_width: int
        @property
        def bubble(self) -> bool:
            return True

    def __init__(self, *, min_width: int = 18, max_width: int = 80, id: str | None = None) -> None:
        super().__init__(id=id)
        self._dragging = False
        self._hovered = False
        self._min = min_width
        self._max = max_width

    def render(self) -> Text:
        if self._dragging or self._hovered:
            return Text("← →", justify="center", style="bold")
        return Text("⇄", justify="center", style="bold")

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
        # jeśli mysz nadal nad handlem, Enter/Leave i tak ogarnie hover,
        # ale bezpiecznie można przywrócić hover tylko jeśli chcesz:
        self.add_class("-hover")
        self.refresh()
        event.stop()

    def on_mouse_move(self, event: MouseMove) -> None:
        if not self._dragging:
            return

        # event.screen_x jest w "komórkach" terminala
        new_width = max(self._min, min(event.screen_x, self._max))
        self.post_message(self.SplitDragged(new_width))
        event.stop()
