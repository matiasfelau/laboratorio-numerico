# utils/parametros.py
from dataclasses import dataclass

@dataclass(frozen=True)
class ConfigMetodo:
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

def resolver_config(
    iteraciones=None,
    tolerancia=None,
    porcentaje=None,
    precision=None,
):
    cfg = ConfigMetodo(
        iteraciones=DEFAULTS.iteraciones if iteraciones is None else iteraciones,
        tolerancia=DEFAULTS.tolerancia if tolerancia is None else tolerancia,
        porcentaje=DEFAULTS.porcentaje if porcentaje is None else porcentaje,
        precision=DEFAULTS.precision if precision is None else precision,
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