from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldDefinition:
    key: str
    label: str
    kind: str
    default: Any
    options: list[str] | None = None


@dataclass(frozen=True)
class MethodDefinition:
    key: str
    label: str
    description: str
    fields: list[FieldDefinition]


def get_methods() -> list[MethodDefinition]:
    return [
        MethodDefinition(
            key="newton_raphson",
            label="Newton-Raphson",
            description="Aproxima una raíz.",
            fields=[
                FieldDefinition("f_expr", "Expresión", "str", ""),
                FieldDefinition("x", "Punto inicial", "float", ""),
                FieldDefinition("tipo", "Tipo de error", "str", "Absoluto", ["Absoluto", "Relativo"]),
            ],
        ),
        MethodDefinition(
            key="biseccion",
            label="Bisección",
            description="Aproxima una raíz.",
            fields=[
                FieldDefinition("f_expr", "Expresión", "str", ""),
                FieldDefinition("a", "Inicio del intervalo", "float", ""),
                FieldDefinition("b", "Final del intervalo", "float", ""),
                FieldDefinition("tipo", "Tipo de error", "str", "Absoluto", ["Absoluto", "Relativo"]),
            ],
        ),
        MethodDefinition(
            key="punto_fijo",
            label="Punto fijo",
            description="Aproxima una raíz.",
            fields=[
                FieldDefinition("g_expr", "Expresión", "str", ""),
                FieldDefinition("x", "Punto inicial", "float", ""),
                FieldDefinition("tipo", "Tipo de error", "str", "Absoluto", ["Absoluto", "Relativo"]),
            ],
        ),
        MethodDefinition(
            key="aceleracion_aitken",
            label="Aceleración de Aitken",
            description="Aproxima una raíz.",
            fields=[
                FieldDefinition("g_expr", "Expresión", "str", ""),
                FieldDefinition("x", "Punto inicial", "float", ""),
                FieldDefinition("tipo", "Tipo de error", "str", "Absoluto", ["Absoluto", "Relativo"]),
            ],
        ),
    ]
