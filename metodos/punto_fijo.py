import numpy as np
from scipy.differentiate import derivative
from tabulate import tabulate

from utils.configuracion import establecer_configuracion

def g(x):
    return np.exp(-x)

def punto_fijo(x, tipo):
    p, calcular_error, criterio_parada = establecer_configuracion(tipo)

    tabla = []

    if abs(derivative(g, x).df) > 1:
        raise ValueError("La función g no es adecuada para el método de punto fijo en el punto inicial dado.")

    for i in range(p.iteraciones):
        gx = round(g(x), p.precision)
        
        error = calcular_error(gx, x)
        
        tabla.append([i + 1, x, gx, error])

        if criterio_parada(error):
            break

        x = gx

    print(tabulate(tabla, headers=["i", "x", "g(x)", "e"], tablefmt="grid", floatfmt=f".{p.precision}f"))

if __name__ == "__main__":
    punto_fijo(1, "absoluto")