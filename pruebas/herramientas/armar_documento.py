#!/usr/bin/env python3
"""Arma el documento Word de la experimentacion a partir de resumen.json y las imagenes.

Uso (desde la raiz del repo): python pruebas/herramientas/armar_documento.py
Requiere python-docx.
"""
import json
import os
import statistics

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

RAIZ = os.getcwd()
IMG = os.path.join(RAIZ, "entrega", "img")
D = json.load(open(os.path.join(RAIZ, "pruebas", "experimentacion", "resultados", "resumen.json"), encoding="utf-8"))


def m(eid, clave):
    return round(statistics.mean(r["total"][clave] for r in D[eid]), 1)


def vals(eid, clave):
    return " y ".join(str(r["total"][clave]) for r in D[eid])


def mon(eid, clave):
    return " y ".join(str(r["monitor"][clave]) for r in D[eid])


def n(x):
    """Numero con separador de miles (punto) y coma decimal."""
    s = f"{x:,.1f}" if isinstance(x, float) and x != int(x) else f"{int(x):,}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


doc = Document()
est = doc.styles["Normal"]
est.font.name = "Calibri"
est.font.size = Pt(11)
for s in doc.sections:
    s.left_margin = s.right_margin = Cm(2.2)
    s.top_margin = s.bottom_margin = Cm(2)


def h(texto, nivel=1):
    doc.add_heading(texto, level=nivel)


def p(texto, negrita=False, cursiva=False):
    par = doc.add_paragraph()
    r = par.add_run(texto)
    r.bold, r.italic = negrita, cursiva
    return par


def li(texto):
    doc.add_paragraph(texto, style="List Bullet")


def img(nombre, ancho=16.5, pie=None):
    ruta = os.path.join(IMG, nombre)
    if os.path.exists(ruta):
        doc.add_picture(ruta, width=Cm(ancho))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if pie:
            c = doc.add_paragraph(pie)
            c.alignment = WD_ALIGN_PARAGRAPH.CENTER
            c.runs[0].italic = True
            c.runs[0].font.size = Pt(9)


def tabla(filas, encabezado):
    t = doc.add_table(rows=1, cols=len(encabezado))
    t.style = "Light Grid Accent 1"
    for i, e in enumerate(encabezado):
        t.rows[0].cells[i].text = e
    for f in filas:
        c = t.add_row().cells
        for i, v in enumerate(f):
            c[i].text = str(v)
    doc.add_paragraph()


def escenario(filas):
    tabla(filas, ["Parámetro", "Valor"])


# ---------------------------------------------------------------- portada
doc.add_heading("Taller de experimentación con JMeter: ¿Qué pasaría si...?", 0)
p("Pruebas de software, taller de rendimiento. Trabajo individual.")
p("Estudiante: Julian Andres Mendoza Castro, código A00395237")
p("Repositorio: monorepo tiquetmania (api/, pruebas/, .github/workflows/). Los planes, los resultados "
  "y los reportes HTML de cada corrida están en pruebas/experimentacion/.")

h("Cómo hice las pruebas")
e = D["q1_20u"][0]["meta"]["entorno"]
li(f"Equipo: {e['nucleos_logicos']} núcleos lógicos, {e['ram_gb']} GB de RAM, {e['so']}. {e['java']}. JMeter 5.6.3.")
li("La API (Python, puerto 8080) y JMeter corren en el mismo computador. Es una limitación de todo el taller.")
li("Todas las corridas son en modo no-GUI, con la API reiniciada antes de cada una, y cada escenario se corrió "
   "dos veces (la prueba de 10 minutos solo una vez). Cambié una variable por escenario.")
li("Los planes están en pruebas/experimentacion/: Experimentacion.jmx (preguntas 1 a 6 y 10), "
   "Experimentacion_concurrencia.jmx (7 y 8) y Experimentacion_validacion.jmx (9). No toqué Ticketmania.jmx. "
   "Cada escenario se arma con propiedades de JMeter (por ejemplo -Jhilos=500), y el comando exacto de cada "
   "corrida quedó guardado en su meta.json.")
li("CPU y memoria los medí con un script en Python (psutil) cada segundo, no con PerfMon y ServerAgent. "
   "El ServerAgent depende de SIGAR, que la presentación de clase advierte que puede no iniciar. "
   "Mide el equipo completo, igual que PerfMon.")
li("La API ticketmania_simple.py no venía en los archivos del taller, así que la escribí siguiendo las reglas "
   "de la presentación (tarifas, precios, pago siempre aprobado, 404 al pagar dos veces la misma reserva).")
li("Rendimiento es peticiones por segundo del reporte de JMeter. Costo es la columna Media en milisegundos. "
   "p95 es el tiempo que cubre al 95 % de las peticiones.")
p("Así se ve el plan en JMeter (el escenario de experimentación se controla con propiedades, por eso los "
  "campos muestran ${__P(hilos,20)} y similares):")
img("gui_exp_grupo_hilos.png", 15, "Grupo de Hilos de Experimentacion.jmx")
img("gui_exp_arbol.png", 15, "Árbol del plan de experimentación, con los controladores por modo")

# ---------------------------------------------------------------- P1
h("Carga")
h("Pregunta 1. ¿Qué pasaría si subo de 20 a 500 usuarios? ¿Cambia el throughput, el tiempo de respuesta o ambos?", 2)
escenario([("Plan", "Experimentacion.jmx, modo flujo completo (tarifas, selección, pago)"),
           ("Hilos", "20 en una corrida, 500 en la otra"), ("Subida", "10 s"),
           ("Duración", "60 s, con bucle infinito"), ("Temporizador", "Aleatorio uniforme, 500 a 1500 ms"),
           ("Repeticiones", "2 por cada valor")])
tabla([("20 usuarios", vals("q1_20u", "rendimiento_s"), vals("q1_20u", "media_ms"), vals("q1_20u", "p95_ms"), vals("q1_20u", "error_pct")),
       ("500 usuarios", vals("q1_500u", "rendimiento_s"), vals("q1_500u", "media_ms"), vals("q1_500u", "p95_ms"), vals("q1_500u", "error_pct"))],
      ["Escenario (dos corridas)", "Rendimiento (peticiones/s)", "Media (ms)", "p95 (ms)", "% Error"])
img("q1.png", 15)
img("reporte_q1_500u.png", 13, "Reporte de JMeter, 500 usuarios (corrida 1)")
p(f"Respuesta: cambia el throughput y el tiempo de respuesta no. Con 20 usuarios el sistema completó unas "
  f"{n(m('q1_20u','rendimiento_s'))} peticiones por segundo y con 500 unas {n(m('q1_500u','rendimiento_s'))}, "
  f"casi 25 veces más, que es lo que se esperaba al tener 25 veces más usuarios. La media se quedó en uno o dos "
  f"milisegundos y no hubo errores. La media incluso salió algo menor con 500 usuarios, y yo no la leería como "
  f"una mejora real, porque son valores muy chicos y la primera prueba incluye el arranque de la JVM.")
p("Limitación: con los temporizadores puestos, cada usuario espera entre 0,5 y 1,5 segundos entre peticiones, así que "
  "el throughput lo marca casi por completo el número de usuarios y no la capacidad de la API. Esta prueba no muestra "
  "hasta dónde aguanta. Tampoco pude separar el efecto del arranque de JMeter en los primeros segundos.", cursiva=True)

# ---------------------------------------------------------------- P2
h("Pregunta 2. ¿Qué pasaría si el ramp-up pasa de 1 segundo a 60 segundos? ¿Cambia el pico inicial del reporte?", 2)
r1, r60 = D["q2_subida1"], D["q2_subida60"]
escenario([("Plan", "Experimentacion.jmx, modo flujo completo"), ("Hilos", "100"),
           ("Subida", "1 s en una corrida, 60 s en la otra"), ("Duración", "120 s"),
           ("Temporizador", "Aleatorio uniforme, 500 a 1500 ms"), ("Repeticiones", "2")])
tabla([("Subida 1 s", " y ".join(str(max(r["rendimiento_por_segundo"][:10])) for r in r1),
        " y ".join(str(round(statistics.mean(r["rendimiento_por_segundo"][:10]), 1)) for r in r1), vals("q2_subida1", "max_ms")),
       ("Subida 60 s", " y ".join(str(max(r["rendimiento_por_segundo"][:10])) for r in r60),
        " y ".join(str(round(statistics.mean(r["rendimiento_por_segundo"][:10]), 1)) for r in r60), vals("q2_subida60", "max_ms"))],
      ["Escenario (dos corridas)", "Máximo en los primeros 10 s (peticiones/s)", "Promedio en los primeros 10 s", "Máx del tiempo de respuesta (ms)"])
img("q2.png", 15)
p("Respuesta: sí cambia el pico inicial. Con subida de 1 segundo los 100 usuarios entran casi juntos y en los primeros "
  "10 segundos hay unas 100 peticiones por segundo, con un máximo de 113 a 115. Con subida de 60 segundos entran poco "
  "a poco y en esos mismos 10 segundos solo hay unas 10 por segundo, con un máximo de 20 a 22. Una vez que todos los "
  "usuarios están dentro, los dos escenarios se igualan en unas 100 peticiones por segundo. El tiempo máximo de "
  "respuesta también fue mayor con la subida corta (128 y 115 ms frente a 23 y 20 ms).")
p("Limitación: el mayor tiempo de respuesta con subida corta puede deberse al arranque de los hilos y de las "
  "conexiones en JMeter y no solo a la API. No lo separé. La prueba de 60 s de subida también tiene menos tiempo "
  "a plena carga dentro de los 120 s.", cursiva=True)

# ---------------------------------------------------------------- P3
h("Pregunta 3. ¿Qué pasaría si quito los temporizadores? ¿Cuánto sube el throughput y qué significa eso para la prueba?", 2)
escenario([("Plan", "Experimentacion.jmx, modo flujo completo"), ("Hilos", "100"), ("Subida", "10 s"),
           ("Duración", "60 s"), ("Temporizador", "Con: aleatorio uniforme 500 a 1500 ms. Sin: constante 0 y aleatorio 0"),
           ("Repeticiones", "2")])
tabla([("Con temporizador", vals("q3_con_temp", "rendimiento_s"), vals("q3_con_temp", "media_ms"), vals("q3_con_temp", "p95_ms")),
       ("Sin temporizador", vals("q3_sin_temp", "rendimiento_s"), vals("q3_sin_temp", "media_ms"), vals("q3_sin_temp", "p95_ms"))],
      ["Escenario (dos corridas)", "Rendimiento (peticiones/s)", "Media (ms)", "p95 (ms)"])
img("q3.png", 15)
img("reporte_q3_sin_temp.png", 13, "Reporte de JMeter sin temporizadores (corrida 1)")
con, sin = m("q3_con_temp", "rendimiento_s"), m("q3_sin_temp", "rendimiento_s")
p(f"Respuesta: el throughput pasó de unas {n(con)} a unas {n(sin)} peticiones por segundo, alrededor de {round(sin/con)} veces más. "
  f"La media también subió, de menos de 1 ms a unos 10 ms, y el p95 pasó de 2 ms a entre 17 y 24 ms. Para la prueba significa "
  f"que el temporizador es lo que fija el ritmo de los usuarios. Con él, 100 usuarios simulan personas que piensan entre "
  f"clics. Sin él, los 100 hilos disparan peticiones lo más rápido que pueden y lo que se mide es el máximo que "
  f"soportan la API y el generador juntos, que es una carga irreal para personas.")
p("Limitación: sin temporizadores el generador y la API compiten por el mismo equipo, así que no puedo decir cuánto del "
  "límite es de la API y cuánto de JMeter. Las dos corridas dieron rendimientos distintos (9.751 y 8.479), por lo que la "
  "cifra tiene una variación de más de 10 %.", cursiva=True)

# ---------------------------------------------------------------- P4
h("Estrés")
h("Pregunta 4. ¿Qué pasaría si escalono de 50 a 100, 250 y 500 usuarios? ¿En qué punto deja de crecer el throughput?", 2)
escenario([("Plan", "Experimentacion.jmx, modo flujo completo"), ("Hilos", "50, 100, 250 y 500 (una corrida por valor)"),
           ("Subida", "10 s"), ("Duración", "60 s por escalón"),
           ("Temporizador", "Ninguno (constante 0 y aleatorio 0), para poder llegar a saturar"),
           ("Repeticiones", "2 por escalón")])
tabla([(f"{u} usuarios", vals(f"q4_{u}", "rendimiento_s"), vals(f"q4_{u}", "media_ms"), vals(f"q4_{u}", "p95_ms"),
        vals(f"q4_{u}", "max_ms"), vals(f"q4_{u}", "error_pct")) for u in (50, 100, 250, 500)],
      ["Escalón (dos corridas)", "Rendimiento (peticiones/s)", "Media (ms)", "p95 (ms)", "Máx (ms)", "% Error"])
img("q4.png", 15)
img("reporte_q4_500.png", 13, "Reporte de JMeter con 500 usuarios (corrida 1): 17 % de errores")
p("Respuesta: el throughput ya estaba en su techo desde el primer escalón. Con 50 usuarios fue de unas 8.200 a 8.500 "
  "peticiones por segundo y con 100, 250 y 500 se mantuvo entre unas 7.600 y 8.800. No crece al subir los usuarios. "
  "Como mi primer escalón ya estaba en el techo, no puedo decir en qué número exacto de usuarios deja de crecer. "
  "Está por debajo de 50. Lo que sí cambia al subir los usuarios es el tiempo de respuesta, que aumenta casi en la misma "
  "proporción: la media va de unos 5,5 ms con 50 usuarios a 11 con 100, 30 con 250 y 52 a 56 con 500. Con 500 aparecen "
  "errores, entre 17 % y 35 % según la corrida, y todos son de tipo Connection refused al puerto 8080, además de unos "
  "pocos 404 en el pago de reservas que no se crearon. Con 250 usuarios no hubo errores.")
p("Limitación: las peticiones rechazadas fallan casi al instante, por eso el rendimiento de 500 usuarios no es comparable "
  "con el de los otros escalones. Las dos corridas de 500 usuarios dieron porcentajes de error muy distintos (17 % y 35 %), "
  "así que esa cifra no es estable. El reporte muestra qué falló (conexión rechazada), pero no medí por qué la API "
  "rechazó conexiones.", cursiva=True)

# ---------------------------------------------------------------- P5
h("Pregunta 5. ¿Qué pasaría si la prueba dura 10 minutos en lugar de 1? ¿El tiempo de respuesta se mantiene o sube con el tiempo?", 2)
escenario([("Plan", "Experimentacion.jmx, modo flujo completo"), ("Hilos", "200"), ("Subida", "30 s"),
           ("Duración", "60 s en una corrida y 600 s en la otra"), ("Temporizador", "Aleatorio uniforme, 500 a 1500 ms"),
           ("Repeticiones", "2 la de 1 minuto, 1 la de 10 minutos")])
r10 = D["q5_10min"][0]
tabla([("1 minuto", vals("q5_1min", "rendimiento_s"), vals("q5_1min", "media_ms"), vals("q5_1min", "p95_ms"), vals("q5_1min", "error_pct")),
       ("10 minutos", m("q5_10min", "rendimiento_s"), m("q5_10min", "media_ms"), m("q5_10min", "p95_ms"), m("q5_10min", "error_pct"))],
      ["Escenario", "Rendimiento (peticiones/s)", "Media (ms)", "p95 (ms)", "% Error"])
img("q5.png", 15)
p("Respuesta: el tiempo de respuesta se mantiene. En los 10 minutos la media por minuto estuvo siempre entre 0,5 y 0,7 ms "
  "y el p95 fue de 1 ms en todos los minutos (la prueba de 1 minuto dio 2 ms, que puede ser el arranque). No hubo errores. La memoria "
  "de la API subió en el primer minuto de unos 27 MB a unos 36 MB y después se quedó estable. El proceso de JMeter llegó a "
  f"unos {int(r10['monitor']['mem_jmeter_max_mb'])} MB y se estabilizó. Esto no muestra una fuga en estos 10 minutos.")
p("Limitación: con 200 usuarios y temporizadores la carga es baja, así que 10 minutos no estresan la API. Una "
  "degradación por tiempo podría aparecer con más carga o durante 30 minutos o más. La memoria de JMeter se "
  "estabiliza en el tamaño del heap de Java y no la tomo como señal de nada.", cursiva=True)

# ---------------------------------------------------------------- P6
h("Pregunta 6. ¿Qué pasaría si mido /api/tarifas (solo lectura) y /api/seleccion (crea reservas) con la misma carga? ¿Cuál cuesta más?", 2)
escenario([("Plan", "Experimentacion.jmx, modo tarifas en una corrida y modo seleccion en la otra"), ("Hilos", "100"),
           ("Subida", "10 s"), ("Duración", "60 s"), ("Temporizador", "Ninguno"), ("Repeticiones", "2")])
tabla([("/api/tarifas", vals("q6_tarifas", "media_ms"), vals("q6_tarifas", "p95_ms"), vals("q6_tarifas", "rendimiento_s")),
       ("/api/seleccion", vals("q6_seleccion", "media_ms"), vals("q6_seleccion", "p95_ms"), vals("q6_seleccion", "rendimiento_s"))],
      ["Petición (dos corridas)", "Media (ms)", "p95 (ms)", "Rendimiento (peticiones/s)"])
img("q6.png", 15)
p(f"Respuesta: /api/seleccion cuesta más. Su media fue de {vals('q6_seleccion','media_ms')} ms frente a {vals('q6_tarifas','media_ms')} ms "
  f"de /api/tarifas, cerca de 40 % más, y su p95 también es mayor. Como consecuencia, con los mismos 100 usuarios se "
  f"completaron menos peticiones por segundo de selección que de tarifas. Uso costo en el sentido del taller, "
  f"el tiempo que tarda la petición.")
p("Limitación: la diferencia es de pocos milisegundos, aunque se repite en las dos corridas (8,3 y 9,5 contra 13,1 y 12,2). "
  "No medí qué parte del código de la API explica la diferencia, así que no sé por qué selección cuesta más.", cursiva=True)

# ---------------------------------------------------------------- P7
h("Concurrencia")
h("Pregunta 7. ¿Qué pasaría si 500 usuarios crean reservas al mismo tiempo? ¿Todas las respuestas son exitosas?", 2)
escenario([("Plan", "Experimentacion_concurrencia.jmx, sincronizado (-Jsync=1)"), ("Hilos", "500, una sola petición cada uno"),
           ("Subida", "0 s"), ("Temporizador", "Sincronizado, grupo de 500"), ("Petición", "POST /api/seleccion"),
           ("Repeticiones", "2")])
q7 = D["q7_sync500"]
tabla([(f"Corrida {r['meta']['repeticion']}", r["total"]["muestras"], r["total"]["errores"], r["total"]["error_pct"],
        r["reservas"]["unicas"] - 1, r["total"]["media_ms"], r["total"]["max_ms"], r["dispersion_inicio_ms"]) for r in q7],
      ["", "Peticiones", "Fallidas", "% Error", "Reservas únicas", "Media (ms)", "Máx (ms)", "Dispersión de inicio (ms)"])
img("reporte_q7_sync500.png", 13, "Reporte de JMeter, 500 reservas simultáneas (corrida 1)")
p("Respuesta: no, no todas fueron exitosas. En las dos corridas fallaron 296 de las 500 peticiones (59,2 %) y solo "
  "204 recibieron una reserva. Los 296 fallos fueron todos Connection refused al puerto 8080: la petición ni siquiera "
  "llegó a la aplicación. Las 204 reservas que sí se crearon tenían identificadores distintos, así que no se pisaron entre sí. "
  "Los 500 hilos arrancaron dentro de una ventana de unos 30 ms.")
p("Limitación: este resultado es de la API de Python y de este equipo, y no sé la causa exacta del rechazo (puede ser la cola "
  "de conexiones pendientes del servidor, pero no la medí). El valor idéntico en las dos corridas (296) sugiere que "
  "algo fijo lo determina, y tampoco lo comprobé.", cursiva=True)

# ---------------------------------------------------------------- P8
h("Pregunta 8. ¿Qué pasaría si los usuarios disparan a la vez con el Temporizador Sincronizado, frente a cuando llegan distribuidos?", 2)
escenario([("Plan", "Experimentacion_concurrencia.jmx"), ("Hilos", "500"),
           ("Sincronizado", "subida 0 s y Temporizador Sincronizado de 500 (la prueba de la pregunta 7)"),
           ("Distribuido", "subida de 30 s, sin sincronizar (-Jsync=0)"), ("Repeticiones", "2")])
q8 = D["q8_distribuido"]
tabla([("Sincronizado", vals("q7_sync500", "error_pct"), vals("q7_sync500", "media_ms"), vals("q7_sync500", "p95_ms"), vals("q7_sync500", "max_ms")),
       ("Distribuido", vals("q8_distribuido", "error_pct"), vals("q8_distribuido", "media_ms"), vals("q8_distribuido", "p95_ms"), vals("q8_distribuido", "max_ms"))],
      ["Escenario (dos corridas)", "% Error", "Media (ms)", "p95 (ms)", "Máx (ms)"])
img("q8.png", 15)
p(f"Respuesta: la diferencia es grande. Sincronizado, 59,2 % de errores y una media de {vals('q7_sync500','media_ms')} ms. "
  f"Distribuido en 30 segundos, 0 % de errores, las 500 reservas únicas y una media de {vals('q8_distribuido','media_ms')} ms. "
  f"Mismas 500 peticiones, y lo único que cambia es si llegan juntas o repartidas. La llegada simultánea es lo que "
  f"hace fallar a la API en este equipo.")
p("Limitación: en el distribuido el rendimiento (unas 17 peticiones por segundo) lo fija el tiempo de subida y no la API. "
  "Tampoco probé valores intermedios (por ejemplo 5 o 10 segundos de subida) para ver desde cuándo empiezan los errores.", cursiva=True)

# ---------------------------------------------------------------- P9
h("Pregunta 9. ¿Qué pasaría si el total cobrado no coincide con precio × cantidad bajo carga? ¿Cómo lo validarías con el CSV?", 2)
escenario([("Plan", "Experimentacion_validacion.jmx"), ("Hilos", "200"), ("Subida", "10 s"), ("Bucles", "5 por usuario"),
           ("CSV", "datos_validacion.csv con las columnas tarifa, cantidad y total_esperado (precio × cantidad ya calculado)"),
           ("Aserción", "JSON Assertion sobre $.total con valor esperado ${total_esperado}, en SeleccionTarifaYCantidad"),
           ("Control", "datos_validacion_error.csv, donde puse mal a propósito el total de 4 de las 20 filas")])
tabla([("Totales correctos", vals("q9_validacion", "muestras"), vals("q9_validacion", "errores")),
       ("Control con 20 % de totales mal", m("q9_control_error", "muestras"), m("q9_control_error", "errores"))],
      ["Escenario", "Muestras (selección y pago)", "Muestras fallidas"])
img("q9.png", 11)
p("Cómo lo validaría con el CSV: en el CSV agrego una columna con el total esperado, que es el precio de la tarifa por la "
  "cantidad de esa fila. JMeter lee la fila, envía la selección y la aserción compara el campo total de la respuesta con "
  "esa columna. Si no coincide, la muestra queda fallida en el reporte.")
p("Respuesta: con 200 usuarios y 1.000 selecciones no hubo ninguna diferencia, los totales siempre coincidieron con "
  "precio por cantidad. Para saber si la aserción de verdad detecta el problema, corrí un control con 4 de las 20 filas "
  "del CSV con el total equivocado: fallaron 200 de las 1.000 selecciones (20 %), justo las de esas filas, y el reporte "
  "marcó 10 % de error sobre el total de muestras. La validación funciona. Bajo esta carga la API calculó bien los totales.")
p("Limitación: la validación solo detecta totales que no coinciden con mi CSV. Si el CSV tuviera un precio equivocado, "
  "lo repetiría. El control lo armé yo con datos mal puestos a propósito, no es un error real de la API. Además, no probé "
  "este flujo con carga que cause rechazos de conexión.", cursiva=True)

# ---------------------------------------------------------------- P10
h("Recursos")
h("Pregunta 10. ¿Qué pasaría si subo a 500 usuarios? ¿Cómo se comportan la memoria y la CPU durante la prueba? ¿Llegan a saturarse? ¿Cuánto cambia el tiempo de respuesta cuando eso pasa?", 2)
escenario([("Plan", "Experimentacion.jmx, modo flujo completo"), ("Hilos", "500 (y 20 como referencia)"), ("Subida", "10 s"),
           ("Duración", "60 s"), ("Temporizador", "Con (500 a 1500 ms) y sin temporizador"),
           ("Medición de equipo", "psutil, una muestra por segundo, equipo completo"), ("Repeticiones", "2")])
tabla([("20 usuarios, con temporizador", mon("q1_20u", "cpu_media_pct"), mon("q1_20u", "cpu_max_pct"), mon("q1_20u", "mem_usada_max_pct"), vals("q1_20u", "media_ms")),
       ("500 usuarios, con temporizador", mon("q1_500u", "cpu_media_pct"), mon("q1_500u", "cpu_max_pct"), mon("q1_500u", "mem_usada_max_pct"), vals("q1_500u", "media_ms")),
       ("500 usuarios, sin temporizador", mon("q4_500", "cpu_media_pct"), mon("q4_500", "cpu_max_pct"), mon("q4_500", "mem_usada_max_pct"), vals("q4_500", "media_ms")),
       ("100 usuarios, sin temporizador", mon("q4_100", "cpu_media_pct"), mon("q4_100", "cpu_max_pct"), mon("q4_100", "mem_usada_max_pct"), vals("q4_100", "media_ms"))],
      ["Escenario (dos corridas)", "CPU media (%)", "CPU máxima (%)", "Memoria usada máx (%)", "Media de respuesta (ms)"])
img("q10.png", 16, "CPU y memoria del equipo completo, corrida 1 de cada escenario")
p(f"Respuesta: con 500 usuarios y temporizadores, el equipo estuvo tranquilo: CPU media de {mon('q1_500u','cpu_media_pct')} % y máxima "
  f"de {mon('q1_500u','cpu_max_pct')} %. Sin temporizadores, la CPU fue más alta, con medias de {mon('q4_500','cpu_media_pct')} % y "
  f"máximos de {mon('q4_500','cpu_max_pct')} %, y llegó a un pico de 94 % en una de las corridas, pero no se mantuvo cerca de 100 %, "
  f"o sea que no la considero saturada. La memoria del equipo usó entre 75 y 83 % de los 24 GB y no creció sin parar. "
  f"El proceso de JMeter llegó a unos 900 a 980 MB y la API a unos 48 MB. El tiempo de respuesta sí cambió mucho con 500 "
  f"usuarios sin temporizador: la media fue de {vals('q4_500','media_ms')} ms contra {vals('q4_100','media_ms')} ms con 100 usuarios "
  f"(casi cinco veces), y el máximo llegó a unos 28 y 39 segundos, con errores de conexión.")
p("Limitación: el cambio de tiempo de respuesta no coincide con una CPU o memoria saturadas del equipo, así que no puedo atribuirlo a "
  "la falta de recursos del computador. Puede deberse a la API (un solo proceso de Python) o al propio generador, y "
  "no lo separé. No pude medir la CPU de la API por separado: mi medición de CPU por proceso devolvió 0 y la descarté. "
  "Solo usé la CPU y la memoria del equipo completo, que mezcla JMeter, la API y todo lo demás que estuviera abierto.", cursiva=True)

# ---------------------------------------------------------------- cierre
h("Limitaciones generales")
li("La API y JMeter comparten computador. En una prueba real la API debe correr sola en un equipo dedicado.")
li("Dos repeticiones por escenario no alcanzan para estadística formal. Donde las dos corridas difieren mucho (por ejemplo, "
   "errores con 500 usuarios) lo dejé dicho.")
li("No definí criterios de aceptación: el taller dice que en este ejercicio no se hacen cumplir.")
li("Medí CPU y memoria con psutil y no con PerfMon y ServerAgent. Es el mismo tipo de dato (equipo completo), pero no es la misma herramienta.")
li("Las capturas del escenario son de la interfaz de JMeter para los planes completos, y de los reportes HTML para cada corrida. "
   "Los parámetros de cada escenario están en su tabla y en el meta.json de la carpeta de resultados.")

h("Anexo: capturas del plan de despliegue (Ticketmania.jmx)")
for nombre, pie in [("gui_02_grupo_hilos.png", "Grupo de Hilos: 200 usuarios, subida 300 s, bucle 1"),
                    ("gui_00_inicio.png", "Plan Ticketmania con datos.csv como ruta relativa"),
                    ("gui_06_asercion_pago.png", "Árbol completo con el temporizador, el extractor y la aserción de Pago")]:
    img(nombre, 14, pie)

os.makedirs(os.path.join(RAIZ, "entrega"), exist_ok=True)
salida = os.path.join(RAIZ, "entrega", "2026.11.16_Experimentacion_JMeter_Que_pasaria_si_v1.docx")
doc.save(salida)
print("guardado", salida)
