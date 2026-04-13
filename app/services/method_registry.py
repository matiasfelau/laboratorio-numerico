"""Registry of methods exposed by the API to the frontend form generator."""

from dataclasses import dataclass
from typing import Any


ERROR_OPTIONS = ["Absoluto", "Relativo"]
FD_METHOD_OPTIONS = ["Progresivo", "Regresivo", "Central"]
INTEGRATION_VARIANT_OPTIONS = ["Simple", "Compuesto"]


@dataclass(frozen=True)
class FieldDefinition:
    """UI field metadata used by the dynamic form renderer."""

    key: str
    label: str
    kind: str
    default: Any
    options: list[str] | None = None
    optional: bool = False


@dataclass(frozen=True)
class MethodDefinition:
    """Method metadata shown in selectors and descriptions."""

    key: str
    label: str
    description: str
    fields: list[FieldDefinition]


def get_methods() -> list[MethodDefinition]:
    """Returns method definitions without changing calculation behavior."""

    return [
        MethodDefinition(
            key="newton_raphson",
            label="Newton-Raphson",
            description="Calcula una aproximación de raíz para f(x)=0.",
            fields=[
                FieldDefinition("f_expr", "Función f(x)", "str", ""),
                FieldDefinition("x", "Punto inicial", "float", ""),
                FieldDefinition("tipo", "Tipo de error", "str", "Absoluto", ERROR_OPTIONS),
            ],
        ),
        MethodDefinition(
            key="biseccion",
            label="Bisección",
            description="Calcula una aproximación de raíz en un intervalo [a, b].",
            fields=[
                FieldDefinition("f_expr", "Función f(x)", "str", ""),
                FieldDefinition("a", "Extremo izquierdo (a)", "float", ""),
                FieldDefinition("b", "Extremo derecho (b)", "float", ""),
                FieldDefinition("tipo", "Tipo de error", "str", "Absoluto", ERROR_OPTIONS),
            ],
        ),
        MethodDefinition(
            key="punto_fijo",
            label="Punto fijo",
            description="Calcula una aproximación de raíz a partir de g(x).",
            fields=[
                FieldDefinition("g_expr", "Función g(x)", "str", ""),
                FieldDefinition("x", "Punto inicial", "float", ""),
                FieldDefinition("tipo", "Tipo de error", "str", "Absoluto", ERROR_OPTIONS),
            ],
        ),
        MethodDefinition(
            key="aceleracion_aitken",
            label="Aceleración de Aitken",
            description="Acelera la convergencia del método de punto fijo.",
            fields=[
                FieldDefinition("g_expr", "Función g(x)", "str", ""),
                FieldDefinition("x", "Punto inicial", "float", ""),
                FieldDefinition("tipo", "Tipo de error", "str", "Absoluto", ERROR_OPTIONS),
            ],
        ),
        MethodDefinition(
            key="lagrange",
            label="Interpolación de Lagrange",
            description="Construye el polinomio interpolante y muestra métricas según el modo seleccionado.",
            fields=[
                FieldDefinition("f_expr", "Función f(x)", "str", "", optional=True),
                FieldDefinition("x_nodos", "Nodos x (separados por coma)", "str", "1, 2, 3"),
                FieldDefinition("y_nodos", "Imágenes y (separadas por coma)", "str", "", optional=True),
                FieldDefinition("x_eval", "Punto de evaluación", "str", "2.5"),
            ],
        ),
        MethodDefinition(
            key="diferencia_finita",
            label="Diferencia finita",
            description="Calcula la derivada aproximada en un punto por expresión o por imágenes.",
            fields=[
                FieldDefinition("f_expr", "Función f(x) (opcional)", "str", "", optional=True),
                FieldDefinition("x", "Punto de evaluación x", "float", "1"),
                FieldDefinition("h", "Paso h", "float", "0.5"),
                FieldDefinition("metodo", "Esquema", "str", "Central", FD_METHOD_OPTIONS),
                FieldDefinition("y_xm1", "Imagen f(x-h) (opcional)", "float", "", optional=True),
                FieldDefinition("y_x", "Imagen f(x) (opcional)", "float", "", optional=True),
                FieldDefinition("y_xp1", "Imagen f(x+h) (opcional)", "float", "", optional=True),
            ],
        ),
        MethodDefinition(
            key="trapecio",
            label="Integración por Trapecio",
            description="Calcula una integral definida usando trapecio simple o compuesto.",
            fields=[
                FieldDefinition("f_expr", "Función f(x)", "str", ""),
                FieldDefinition("a", "Límite inferior (a)", "float", ""),
                FieldDefinition("b", "Límite superior (b)", "float", ""),
                FieldDefinition("variante", "Variante", "str", "Simple", INTEGRATION_VARIANT_OPTIONS),
                FieldDefinition("n", "Subintervalos n (solo compuesto)", "str", "", optional=True),
            ],
        ),
        MethodDefinition(
            key="simpson_13",
            label="Integración por Simpson 1/3",
            description="Calcula una integral definida usando Simpson 1/3 simple o compuesto.",
            fields=[
                FieldDefinition("f_expr", "Función f(x)", "str", ""),
                FieldDefinition("a", "Límite inferior (a)", "float", ""),
                FieldDefinition("b", "Límite superior (b)", "float", ""),
                FieldDefinition("variante", "Variante", "str", "Simple", INTEGRATION_VARIANT_OPTIONS),
                FieldDefinition("n", "Subintervalos n (solo compuesto)", "str", "", optional=True),
            ],
        ),
        MethodDefinition(
            key="simpson_38",
            label="Integración por Simpson 3/8",
            description="Calcula una integral definida usando Simpson 3/8 simple o compuesto.",
            fields=[
                FieldDefinition("f_expr", "Función f(x)", "str", ""),
                FieldDefinition("a", "Límite inferior (a)", "float", ""),
                FieldDefinition("b", "Límite superior (b)", "float", ""),
                FieldDefinition("variante", "Variante", "str", "Simple", INTEGRATION_VARIANT_OPTIONS),
                FieldDefinition("n", "Subintervalos n (solo compuesto)", "str", "", optional=True),
            ],
        ),
    ]
