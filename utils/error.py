"""Error calculation and stop criteria factories used by iterative methods."""


def definir_calculo_error(tipo, precision):
    """Returns error function according to selected type (absoluto/relativo)."""
    calcular_error = None

    if tipo == "relativo":
        def calcular_error(xn, x):
            if xn == 0:
                raise ValueError("El valor de xn es cero. No se puede calcular el error relativo.")

            return round((abs(xn - x) / abs(xn)) * 100, precision)

    elif tipo == "absoluto":
        def calcular_error(xn, x):
            return round(abs(xn - x), precision)

    else:
        raise ValueError("Tipo de error no válido.")

    return calcular_error


def definir_criterio_parada(tipo, tolerancia, porcentaje):
    """Returns stop predicate compatible with the selected error type."""
    criterio_parada = None

    if tipo == "absoluto":
        def criterio_parada(error):
            return error < tolerancia

    elif tipo == "relativo":
        def criterio_parada(error):
            return error < porcentaje

    else:
        raise ValueError("Tipo de error no válido.")

    return criterio_parada