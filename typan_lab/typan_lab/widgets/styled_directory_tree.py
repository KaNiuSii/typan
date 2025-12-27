from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from rich.style import Style
from rich.text import Text
from textual.widgets import DirectoryTree

TagStyle = Tuple[str, Union[str, List[str]]]

FILE_TAGS: Dict[str, TagStyle] = {
    ".py": ("PY", ["dodger_blue1", "orange3"]),
    ".ty": ("TY", ["purple", "dodger_blue1"]),
    ".json": ("JSON", "yellow"),
}

TAG_WIDTH = 4

DEFAULT_FILE_ICON = "📄"

PAD_CHAR = "·"
PAD_STYLE = "dim"

DIRTY_MARK = "●"
DIRTY_STYLE = "red"

ACTIVE_STYLE = "bold"


class StyledDirectoryTree(DirectoryTree):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._dirty_by_file: dict[str, bool] = {}
        self._active_file: str | None = None

    # ---------------- public API ----------------

    def set_active_file(self, path: Path | None) -> None:
        self._active_file = self._key(path) if path else None
        self._invalidate_labels()

    def set_dirty_map(self, dirty_by_file: dict[Path, bool]) -> None:
        self._dirty_by_file = {self._key(p): bool(v) for p, v in dirty_by_file.items()}
        self._invalidate_labels()

    # ---------------- internals ----------------

    @staticmethod
    def _key(path: Path) -> str:
        return path.resolve().as_posix()

    def _invalidate_labels(self) -> None:
        """Wymuś przebudowę labeli.
        Sam refresh() bywa za słaby, bo Tree cache’uje linie/label width.
        """
        try:
            self._clear_line_cache()  # type: ignore[attr-defined]
        except Exception:
            pass

        try:
            self._tree_lines_cached = None  # type: ignore[attr-defined]
        except Exception:
            pass

        self.refresh()

    # ---------------- rendering ----------------

    def render_label(self, node: Any, base_style: Style, style: Style) -> Text:
        path = Path(getattr(node.data, "path", ""))

        if path.is_dir():
            return super().render_label(node, base_style, style)

        ext = path.suffix.lower()

        # lewa kolumna: tag albo ikonka
        if ext in FILE_TAGS:
            tag, tag_style = FILE_TAGS[ext]
            left = self._styled_tag(tag, tag_style)
        else:
            left = Text(DEFAULT_FILE_ICON)

        pad = TAG_WIDTH - left.cell_len
        if pad > 0:
            left.append(PAD_CHAR * pad, style=PAD_STYLE)

        pkey = self._key(path)
        is_dirty = bool(self._dirty_by_file.get(pkey, False))
        is_active = (self._active_file is not None and pkey == self._active_file)

        label = Text()
        label.append_text(left)
        label.append(" ")

        if is_dirty:
            label.append(DIRTY_MARK)
        else:
            label.append(" ")

        label.append(" ")
        label.append(path.name)

        if is_active:
            label.stylize(ACTIVE_STYLE)

        return label

    @staticmethod
    def _styled_tag(tag: str, tag_style: Union[str, List[str]]) -> Text:
        out = Text()

        if isinstance(tag_style, str):
            out.append(tag, style=tag_style)
            return out

        for i, ch in enumerate(tag):
            color = tag_style[i] if i < len(tag_style) else ""
            out.append(ch, style=color)

        return out
