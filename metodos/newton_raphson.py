import numpy as np
from scipy.differentiate import derivative
from tabulate import tabulate

from utils.configuracion import establecer_configuracion


def f(x):
    return x * np.exp(-x)

def newton_raphson(x, tipo="absoluto"):
    p, calcular_error, criterio_parada = establecer_configuracion(tipo)

    tabla = []

    for i in range(p.iteraciones):
        fx = round(f(x), p.precision)
        dx = round(derivative(f, x).df, p.precision)

        if dx == 0:
            raise ValueError("La derivada es cero. No se puede continuar con el método de Newton-Raphson.")

        xn = round(x - fx / dx, p.precision)

        error = calcular_error(xn, x)

        tabla.append([i + 1, x, fx, dx, xn, error])

        if criterio_parada(error):
            break

        x = xn

    print(tabulate(tabla, headers=["i", "xn", "f(xn)", "f'(xn)", "xn+1", "e"], tablefmt="grid", floatfmt=f".{p.precision}f"))

if __name__ == "__main__":
    newton_raphson(-1)