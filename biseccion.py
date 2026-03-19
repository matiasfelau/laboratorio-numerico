import numpy as np
from tabulate import tabulate

from utils.configuracion import establecer_configuracion

def f(x):
    return np.sqrt(x) - np.cos(x)

def biseccion(f, a, b, tipo):
    p, calcular_error, criterio_parada = establecer_configuracion(tipo)
    
    condicion = f(a) * f(b)

    if condicion > 0:
        raise ValueError("La función debe tener signos opuestos en a y b.")

    elif condicion == 0:
        raise ValueError("La función tiene una raíz en uno de los extremos a o b.")


    c = 0
    tabla = []

    for i in range(p.iteraciones):
        cn = round((a + b) / 2, p.precision)
        fc = round(f(cn), p.precision)

        error = calcular_error(cn, c)

        tabla.append([i + 1, a, b, cn, fc, error])

        if criterio_parada(error):
            break

        if f(a) * fc < 0:
            b = cn

        else:
            a = cn

        c = cn

    print(tabulate(tabla, headers=["i", "a", "b", "c", "f(c)", "e"], tablefmt="grid", floatfmt=f".{p.precision}f"))

biseccion(f, 0, 1)