"""Ambiente Jinja2 condiviso e helper di rendering per le pagine HTML.

Usato sia dalla dashboard FastAPI (`api/app.py`) sia dal report HTML su file
(`reports/html_report.py`), così presentazione e logica restano disaccoppiate.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_PACKAGE_ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = _PACKAGE_ROOT / "templates"
STATIC_DIR = _PACKAGE_ROOT / "static"


def security_class(score: object) -> str:
    """Classe CSS (sec-good/sec-warn/sec-bad/sec-unknown) per un punteggio.

    >= 80 buono · 50-79 attenzione · < 50 critico · non numerico sconosciuto.
    """
    if isinstance(score, bool) or not isinstance(score, (int, float, str)):
        return "sec-unknown"
    try:
        value = int(score)
    except (TypeError, ValueError):
        return "sec-unknown"
    if value >= 80:
        return "sec-good"
    if value >= 50:
        return "sec-warn"
    return "sec-bad"


@lru_cache(maxsize=1)
def get_environment() -> Environment:
    """Restituisce l'ambiente Jinja2 (cache singleton)."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["security_class"] = security_class
    return env


def render(template_name: str, **context: object) -> str:
    """Renderizza un template per nome con il contesto fornito."""
    return get_environment().get_template(template_name).render(**context)
