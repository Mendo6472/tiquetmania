# Tiquetmania: pruebas de rendimiento con JMeter

Monorepo del taller de pruebas de software. Contiene la API de Tiquetmania, los planes de JMeter
y el pipeline de GitHub Actions. Trabajo individual.

## Estructura

```
api/ticketmania_simple.py          API (Python, sin librerias externas), puerto 8080
pruebas/jmeter/                    Ejercicio 1: despliegue (lo ejecuta el pipeline)
  Ticketmania.jmx
  datos.csv                        misma carpeta que el .jmx, ruta relativa
pruebas/experimentacion/           Ejercicio 2: "Que pasaria si..." (solo local, el pipeline no lo ejecuta)
  Experimentacion*.jmx, datos*.csv
  resultados/                      jtl, reportes HTML y monitoreo de cada corrida
pruebas/herramientas/              generar_jmx.py, ejecutar_experimentos.py, analizar.py
.github/workflows/rendimiento.yml  pipeline
entrega/                           documento de la experimentacion (Word) y graficas
```

## Ejercicio 1: despliegue

Escenario fijo: Grupo de Hilos estandar, 200 hilos, subida de 300 s, bucle 1 y Temporizador Aleatorio
Uniforme de 500 a 1500 ms (desplazamiento 500, aleatorio 1000). Flujo: `GET /api/tarifas`,
`POST /api/seleccion` (con Extractor JSON a `num_reserva`) y `POST /api/pago` (con Aserción JSON
`estado = APROBADO`). El CSV se lee con la ruta relativa `datos.csv`.

El pipeline (`.github/workflows/rendimiento.yml`) corre con cada push a `main` o a mano con
`workflow_dispatch`. Instala Java 17 y JMeter 5.6.3, levanta la API y espera a `/api/salud`, ejecuta
JMeter en modo no-GUI desde `pruebas/jmeter/`, revisa el `.jtl` y termina en rojo si hay muestras
fallidas, y sube el reporte HTML como artefacto `reporte-rendimiento` aunque algo falle.

Para correrlo en local:

```bash
python api/ticketmania_simple.py &
cd pruebas/jmeter
jmeter -n -t Ticketmania.jmx -l resultados.jtl -e -o reporte
```

En GitHub Actions la API y JMeter comparten la misma maquina virtual. Esta ejecucion comprueba que la
carga corre de principio a fin y no mide la capacidad de la API.

## Ejercicio 2: experimentacion

Responde las 10 preguntas "Que pasaria si..." con JMeter en local. Cada escenario se parametriza con
propiedades (`-Jhilos=500`, etc.) sobre los planes de `pruebas/experimentacion/`. Para repetir todo:

```bash
pip install psutil matplotlib
python pruebas/herramientas/ejecutar_experimentos.py
python pruebas/herramientas/analizar.py
```

El monitoreo de CPU y memoria se hizo con `psutil` (un dato por segundo) y no con PerfMon y ServerAgent.
Los reportes HTML no se versionan (pesan mucho): se regeneran al correr los scripts y hay capturas en `entrega/img/`. El documento con las respuestas, los escenarios, las graficas y las limitaciones esta en `entrega/`.

Limitacion general: la API y JMeter corren en el mismo computador.
