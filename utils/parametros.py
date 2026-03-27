"""Global runtime parameters shared by numeric methods.

The context manager allows web requests to temporarily override defaults
without mutating method implementations.
"""

from contextlib import contextmanager
from dataclasses import dataclass

@dataclass(frozen=True)
class ConfigMetodo:
    """Resolved configuration consumed by numeric algorithms."""

    iteraciones: int
    tolerancia: float
    porcentaje: float
    precision: int

DEFAULTS = ConfigMetodo(
    iteraciones=100,
    tolerancia=1e-6,
    porcentaje=1.0,
    precision=8,
)

_RUNTIME_OVERRIDES: dict[str, int | float] = {}


@contextmanager
def aplicar_configuracion_global(overrides: dict[str, int | float] | None):
    """Temporarily applies request-level overrides during one execution."""
    global _RUNTIME_OVERRIDES

    previous = _RUNTIME_OVERRIDES.copy()
    _RUNTIME_OVERRIDES = _normalizar_overrides(overrides)
    try:
        yield
    finally:
        _RUNTIME_OVERRIDES = previous


def _normalizar_overrides(overrides: dict[str, int | float] | None) -> dict[str, int | float]:
    if not overrides:
        return {}

    clean: dict[str, int | float] = {}
    for key in ("iteraciones", "tolerancia", "porcentaje", "precision"):
        value = overrides.get(key)
        if value is None:
            continue
        clean[key] = value
    return clean


def resolver_config(
    iteraciones=None,
    tolerancia=None,
    porcentaje=None,
    precision=None,
):
    """Resolves effective config from defaults, runtime overrides and explicit args."""
    cfg = ConfigMetodo(
        iteraciones=(
            _RUNTIME_OVERRIDES.get("iteraciones", DEFAULTS.iteraciones)
            if iteraciones is None
            else iteraciones
        ),
        tolerancia=(
            _RUNTIME_OVERRIDES.get("tolerancia", DEFAULTS.tolerancia)
            if tolerancia is None
            else tolerancia
        ),
        porcentaje=(
            _RUNTIME_OVERRIDES.get("porcentaje", DEFAULTS.porcentaje)
            if porcentaje is None
            else porcentaje
        ),
        precision=(
            _RUNTIME_OVERRIDES.get("precision", DEFAULTS.precision)
            if precision is None
            else precision
        ),
    )

    if cfg.iteraciones <= 0:
        raise ValueError("La cantidad de iteraciones debe ser > 0")

    if cfg.tolerancia <= 0:
        raise ValueError("La tolerancia debe ser > 0")

    if cfg.porcentaje <= 0:
        raise ValueError("El porcentaje debe ser > 0")

    if cfg.precision < 0:
        raise ValueError("La precision debe ser >= 0")

    return cfg