from __future__ import annotations

import re

# Usuń CSI: ESC [ ... letter
_CSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
# Usuń OSC: ESC ] ... BEL lub ESC \
_OSC = re.compile(r"\x1b\].*?(?:\x07|\x1b\\)")
# Usuń pojedyncze ESC <char>
_ESC = re.compile(r"\x1b[@-Z\\-_]")

def strip_ansi(text: str) -> str:
    text = _OSC.sub("", text)
    text = _CSI.sub("", text)
    text = _ESC.sub("", text)
    return text
