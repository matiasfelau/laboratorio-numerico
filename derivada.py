import sympy as sp
from tabulate import tabulate
import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt

EXPRESION_TEXTO = "(x + 1) ** (1 / 3)"
VARIABLE_TEXTO = "x"


def calcular_derivada(expresion_texto, variable_texto="x"):
    variable = sp.Symbol(variable_texto)
    expresion = sp.sympify(expresion_texto)
    derivada = sp.diff(expresion, variable)
    derivada_simplificada = sp.simplify(derivada)
    return expresion, derivada, derivada_simplificada


def mostrar_hoja(expresion, variable, derivada, derivada_simplificada):
    hoja = [
        ["Expresion", str(expresion)],
        ["Variable", str(variable)],
        ["Derivada", str(derivada)],
        ["Derivada simplificada", str(derivada_simplificada)],
    ]

    print("\nHoja de resultados")
    print(tabulate(hoja, headers=["Campo", "Valor"], tablefmt="grid"))


def mostrar_hoja_latex(expresion, variable, derivada, derivada_simplificada):
    latex_expresion = sp.latex(expresion)
    latex_derivada = sp.latex(derivada)
    latex_derivada_simplificada = sp.latex(derivada_simplificada)

    lineas = [
        rf"$f({variable}) = {latex_expresion}$",
        rf"$f'({variable}) = {latex_derivada}$",
        rf"$f'_{{simp}}({variable}) = {latex_derivada_simplificada}$",
    ]

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.set_facecolor("#f8f9fb")
    ax.axis("off")

    ax.text(0.02, 0.9, "Hoja de derivacion (LaTeX)", fontsize=16, fontweight="bold")

    for indice, linea in enumerate(lineas):
        ax.text(0.04, 0.72 - indice * 0.23, linea, fontsize=15)

    fig.tight_layout()

    # Mostrar la ventana del plot
    plt.show()


def main():
    print("Calculadora de derivadas")
    print(f"Expresion hardcodeada: {EXPRESION_TEXTO}")
    print(f"Variable hardcodeada: {VARIABLE_TEXTO}")

    try:
        expresion, derivada, derivada_simplificada = calcular_derivada(
            EXPRESION_TEXTO, VARIABLE_TEXTO
        )

        mostrar_hoja(
            expresion,
            sp.Symbol(VARIABLE_TEXTO),
            derivada,
            derivada_simplificada,
        )

        mostrar_hoja_latex(
            expresion,
            sp.Symbol(VARIABLE_TEXTO),
            derivada,
            derivada_simplificada,
        )

    except Exception as error:
        print(f"Error al procesar la expresion: {error}")


if __name__ == "__main__":
    main()