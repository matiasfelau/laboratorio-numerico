from utils.error import definir_calculo_error, definir_criterio_parada
from utils.parametros import resolver_config

def establecer_configuracion(tipo):
    p = resolver_config()

    calcular_error = definir_calculo_error(tipo, p.precision)

    criterio_parada = definir_criterio_parada(tipo, p.tolerancia, p.porcentaje)
    
    return p, calcular_error, criterio_parada