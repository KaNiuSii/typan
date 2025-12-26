from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Iterable
import importlib.resources as ir

def _read_text(package: str, filename: str) -> str:
    """Czyta tekst z zasobów pakietu (działa też w zip/EXE scenariuszach)."""
    return resources.files(package).joinpath(filename).read_text(encoding="utf-8")


def load_tcss(
    *,
    theme: Iterable[tuple[str, str]] = (),
    components: Iterable[tuple[str, str]] = (),
) -> str:
    """
    Ładuje i agreguje TCSS.

    theme/components: iterable (package, filename)
    Przykład: ("typan_lab.screens", "welcome.tcss")
    """
    chunks: list[str] = []

    # Najpierw theme/base (zmienne, globalne style)
    for pkg, file in theme:
        css = _read_text(pkg, file)
        chunks.append(f"/* --- {pkg}/{file} --- */\n{css}\n")

    # Potem style komponentów
    for pkg, file in components:
        css = _read_text(pkg, file)
        chunks.append(f"/* --- {pkg}/{file} --- */\n{css}\n")

    return "\n".join(chunks)


def discover_tcss_near_py(
    package: str,
    *,
    subpackages: Iterable[str],
) -> list[tuple[str, str]]:
    """
    Szuka plików .tcss w podanych subpackages (np. screens, widgets).
    Zwraca listę (package_name, filename) w kolejności alfabetycznej.

    Założenie: tcss leży bezpośrednio w folderze subpackage (nie rekurencyjnie).
    """
    found: list[tuple[str, str]] = []
    for sub in subpackages:
        pkg_name = f"{package}.{sub}"
        root = resources.files(pkg_name)
        for item in root.iterdir():
            if item.is_file() and item.name.endswith(".tcss"):
                found.append((pkg_name, item.name))
    found.sort(key=lambda x: (x[0], x[1]))
    return found

if __name__ == "__main__":
    _COMPONENT_REL = discover_tcss_near_py("typan_lab", subpackages=("screens", "widgets"))
    _CSS_FILES = [str(ir.files(mod) / fname) for (mod, fname) in _COMPONENT_REL]

    print(_COMPONENT_REL)
    print(_CSS_FILES)