import numpy as np
from tabulate import tabulate

def g(x):
    return (x + 1) ** (1 / 3)

def dg(x):
    return 1/(3*(x + 1)**(2/3))

def punto_fijo(g, dg, x, iteraciones=100, tolerancia=1e-6, precision=5):
    tabla = []

    if abs(dg(x)) > 1:
        raise ValueError("La función g no es adecuada para el método de punto fijo en el punto inicial dado.")

    for i in range(iteraciones):
        gx = round(g(x), precision)
        error = round(abs(gx - x), precision)
        
        tabla.append([i + 1, x, gx, error])

        if error < tolerancia:
            break

        x = gx

    print(tabulate(tabla, headers=["i", "x", "g(x)", "e"], tablefmt="grid", floatfmt=f".{precision}f"))
    return gx

punto_fijo(g, dg, 1)