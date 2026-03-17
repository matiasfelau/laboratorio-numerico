import numpy as np
from tabulate import tabulate

def f(x):
    return np.exp(x) - x - 2

#TODO: Consultar si en este método conviene usar el error absoluto.
def biseccion(f, a, b, iteraciones=100, tolerancia=1e-6, precision=6):
    condicion = f(a) * f(b)

    if condicion > 0:
        raise ValueError("La función debe tener signos opuestos en a y b.")
    elif condicion == 0:
        raise ValueError("La función tiene una raíz en uno de los extremos a o b.")

    tabla = []
    for i in range(iteraciones):
        c = round((a + b) / 2, precision)
        fa = round(f(a), precision)
        fb = round(f(b), precision)
        fc = round(f(c), precision)
        error = round(abs(fc), precision)

        tabla.append([i + 1, a, b, c, fa, fb, fc, error])

        if error < tolerancia or (b - a) / 2 < tolerancia:
            break

        if fa * fc < 0:
            b = c
        else:
            a = c

    print(tabulate(tabla, headers=["i", "a", "b", "c", "f(a)", "f(b)", "f(c)", "e"], tablefmt="grid", floatfmt=f".{precision}f"))
    return c

biseccion(f, 1, 2)