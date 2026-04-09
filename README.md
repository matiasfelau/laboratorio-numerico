# Simulador de Metodos Numericos

Aplicacion web para ejecutar y visualizar metodos numericos de la materia Modelado y Simulacion.

## Objetivos de calidad aplicados

- Bajo acoplamiento y alta cohesion en capa de servicios.
- KISS y DRY en validacion/parsing compartido.
- Separacion clara entre:
  - Metodos numericos (`metodos/`)
  - Orquestacion de ejecucion (`app/services/`)
  - API web y visualizacion (`webapp/`)
  - Configuracion de parametros y errores (`utils/`)
- Documentacion en modulos y funciones clave.

## Restricciones funcionales (no regresion)

Estas reglas se consideran contrato del proyecto:

1. No modificar la logica matematica de los metodos numericos ya validados.
2. En metodos iterativos con tabla, el valor redondeado registrado en la tabla es el valor usado en la iteracion siguiente.
3. No cambiar los tipos de error disponibles por metodo.
4. Mantener aclaraciones docentes/ejercicios ya incorporadas:
   - Diferencias finitas sin iteracion cuando corresponde.
   - Cota teorica en error global de Lagrange.
5. No modificar la UI validada salvo pedido explicito.

## Estructura

- `webapp/server.py`: Flask app, endpoints y construccion de trazas para graficos.
- `app/services/method_runner.py`: parsing de entradas, validaciones y despacho de metodos.
- `app/services/method_registry.py`: metadata de metodos y campos para frontend.
- `metodos/`: implementaciones numericas (caja negra para la capa web).
- `utils/parametros.py`: defaults, overrides runtime y validacion de configuracion.
- `utils/error.py`: fabrica de calculo de error y criterios de parada.
- `webapp/static/`, `webapp/templates/`: frontend validado.

## Ejecucion local (Windows)

1. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

2. Iniciar servidor:

```powershell
.\iniciar-servidor.bat
```

3. Abrir en navegador:

- `http://127.0.0.1:5000`

Para detener el servidor, usar `Ctrl+C` en la consola donde se ejecuto.

## Ejecucion con Docker

1. Construir imagen:

```powershell
docker build -t simulador-modelado .
```

2. Ejecutar contenedor:

```powershell
docker run --rm -p 5000:5000 simulador-modelado
```

Alternativa con Docker Compose:

```powershell
docker compose up --build
```

Abrir en navegador:

- `http://127.0.0.1:5000`

## Desarrollo

- Con Flask en debug, cambios en codigo/plantillas suelen reflejarse con recarga de pagina.
- Si hay cache en CSS/JS, usar recarga forzada (`Ctrl+F5`).
- Cualquier refactor futuro debe preservar las reglas de no regresion listadas arriba.
