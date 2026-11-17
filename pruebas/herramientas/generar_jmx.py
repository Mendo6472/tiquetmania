#!/usr/bin/env python3
"""Genera los planes .jmx del taller (JMeter 5.6.3).

Los planes se pueden abrir y editar en la GUI de JMeter. Este script solo
existe para que la estructura quede reproducible y revisable en el repositorio.

Uso: python generar_jmx.py   (desde la raiz del repositorio)
"""
from xml.sax.saxutils import escape


def s(nombre, valor):
    return f'<stringProp name="{nombre}">{escape(str(valor))}</stringProp>'


def b(nombre, valor):
    return f'<boolProp name="{nombre}">{"true" if valor else "false"}</boolProp>'


def arbol(elemento, hijos=""):
    return f"{elemento}\n<hashTree>\n{hijos}</hashTree>\n"


def plan(nombre, hijos):
    cabecera = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">\n<hashTree>\n'
    )
    el = (
        f'<TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="{escape(nombre)}" enabled="true">\n'
        + s("TestPlan.comments", "Plan generado para el taller de rendimiento de Tiquetmania")
        + b("TestPlan.functional_mode", False)
        + b("TestPlan.tearDown_on_shutdown", True)
        + b("TestPlan.serialize_threadgroups", False)
        + '<elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" '
        'testclass="Arguments" testname="Variables definidas por el usuario" enabled="true">'
        '<collectionProp name="Arguments.arguments"/></elementProp>\n'
        + s("TestPlan.user_define_classpath", "")
        + "</TestPlan>"
    )
    return cabecera + arbol(el, hijos) + "</hashTree>\n</jmeterTestPlan>\n"


def valores_por_defecto():
    el = (
        '<ConfigTestElement guiclass="HttpDefaultsGui" testclass="ConfigTestElement" '
        'testname="Valores por Defecto para Peticion HTTP" enabled="true">\n'
        '<elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" '
        'testclass="Arguments" testname="Variables definidas por el usuario" enabled="true">'
        '<collectionProp name="Arguments.arguments"/></elementProp>\n'
        + s("HTTPSampler.domain", "${__P(host,127.0.0.1)}")
        + s("HTTPSampler.port", "${__P(puerto,8080)}")
        + s("HTTPSampler.protocol", "http")
        + "</ConfigTestElement>"
    )
    return arbol(el)


def csv(archivo, variables):
    el = (
        '<CSVDataSet guiclass="TestBeanGUI" testclass="CSVDataSet" '
        'testname="Configuracion del CSV Data Set" enabled="true">\n'
        + s("delimiter", ",")
        + s("fileEncoding", "UTF-8")
        + s("filename", archivo)
        + b("ignoreFirstLine", True)
        + b("quotedData", False)
        + b("recycle", True)
        + s("shareMode", "shareMode.all")
        + b("stopThread", False)
        + s("variableNames", variables)
        + "</CSVDataSet>"
    )
    return arbol(el)


def cabeceras(nombre="Gestor de Cabecera HTTP"):
    def fila(n, v):
        return ('<elementProp name="" elementType="Header">' + s("Header.name", n) + s("Header.value", v)
                + "</elementProp>")
    el = (
        f'<HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="{nombre}" enabled="true">'
        '<collectionProp name="HeaderManager.headers">'
        + fila("Accept", "application/json") + fila("Content-Type", "application/json")
        + "</collectionProp></HeaderManager>"
    )
    return arbol(el)


def peticion(nombre, metodo, ruta, cuerpo=None, hijos="", habilitado=True):
    if cuerpo is None:
        args = ('<elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" '
                'testclass="Arguments" testname="Variables definidas por el usuario" enabled="true">'
                '<collectionProp name="Arguments.arguments"/></elementProp>\n')
    else:
        args = ('<elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" '
                'testclass="Arguments" testname="Variables definidas por el usuario" enabled="true">'
                '<collectionProp name="Arguments.arguments">'
                '<elementProp name="" elementType="HTTPArgument">'
                + b("HTTPArgument.always_encode", False)
                + s("Argument.value", cuerpo) + s("Argument.metadata", "=")
                + "</elementProp></collectionProp></elementProp>\n")
    el = (
        f'<HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{escape(nombre)}" '
        f'enabled="{"true" if habilitado else "false"}">\n'
        + (b("HTTPSampler.postBodyRaw", True) if cuerpo is not None else "")
        + args
        + s("HTTPSampler.path", ruta)
        + s("HTTPSampler.method", metodo)
        + b("HTTPSampler.follow_redirects", True)
        + b("HTTPSampler.auto_redirects", False)
        + b("HTTPSampler.use_keepalive", True)
        + b("HTTPSampler.DO_MULTIPART_POST", False)
        + "</HTTPSamplerProxy>"
    )
    return arbol(el, hijos)


def extractor_reserva():
    el = (
        '<JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" '
        'testname="Extractor JSON: num_reserva" enabled="true">\n'
        + s("JSONPostProcessor.referenceNames", "num_reserva")
        + s("JSONPostProcessor.jsonPathExprs", "$.reserva")
        + s("JSONPostProcessor.match_numbers", "1")
        + s("JSONPostProcessor.defaultValues", "num_reserva_not_found")
        + "</JSONPostProcessor>"
    )
    return arbol(el)


def asercion_json(nombre, ruta, esperado, validar_valor=True):
    el = (
        f'<JSONPathAssertion guiclass="JSONPathAssertionGui" testclass="JSONPathAssertion" '
        f'testname="{escape(nombre)}" enabled="true">\n'
        + s("JSON_PATH", ruta) + s("EXPECTED_VALUE", esperado)
        + b("JSONVALIDATION", validar_valor) + b("EXPECT_NULL", False) + b("INVERT", False) + b("ISREGEX", False)
        + "</JSONPathAssertion>"
    )
    return arbol(el)


def temporizador_aleatorio(constante, aleatorio, nombre="Temporizador Aleatorio Uniforme"):
    el = (
        f'<UniformRandomTimer guiclass="UniformRandomTimerGui" testclass="UniformRandomTimer" '
        f'testname="{nombre}" enabled="true">\n'
        + s("ConstantTimer.delay", constante) + s("RandomTimer.range", aleatorio)
        + "</UniformRandomTimer>"
    )
    return arbol(el)


def temporizador_sincronizado(usuarios, espera_ms=60000):
    el = (
        '<SyncTimer guiclass="TestBeanGUI" testclass="SyncTimer" '
        'testname="Temporizador Sincronizado" enabled="true">\n'
        f'<stringProp name="groupSize">{usuarios}</stringProp>\n'
        f'<stringProp name="timeoutInMs">{espera_ms}</stringProp>\n'
        "</SyncTimer>"
    )
    return arbol(el)


def debug_sampler(habilitado=False):
    el = (
        '<DebugSampler guiclass="TestBeanGUI" testclass="DebugSampler" testname="Debug Sampler" '
        f'enabled="{"true" if habilitado else "false"}">\n'
        + b("displayJMeterProperties", False) + b("displayJMeterVariables", True)
        + b("displaySystemProperties", False)
        + "</DebugSampler>"
    )
    return arbol(el)


def reporte_resumen():
    el = (
        '<ResultCollector guiclass="SummaryReport" testclass="ResultCollector" testname="Reporte resumen" '
        'enabled="true">\n'
        + b("ResultCollector.error_logging", False)
        + '<objProp><name>saveConfig</name><value class="SampleSaveConfiguration">'
        "<time>true</time><latency>true</latency><timestamp>true</timestamp><success>true</success>"
        "<label>true</label><code>true</code><message>true</message><threadName>true</threadName>"
        "<dataType>true</dataType><encoding>false</encoding><assertions>true</assertions>"
        "<subresults>true</subresults><responseData>false</responseData><samplerData>false</samplerData>"
        "<xml>false</xml><fieldNames>true</fieldNames><responseHeaders>false</responseHeaders>"
        "<requestHeaders>false</requestHeaders><responseDataOnError>false</responseDataOnError>"
        "<saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>"
        "<assertionsResultsToSave>0</assertionsResultsToSave><bytes>true</bytes><sentBytes>true</sentBytes>"
        "<url>true</url><threadCounts>true</threadCounts><idleTime>true</idleTime>"
        "<connectTime>true</connectTime></value></objProp>\n"
        + s("filename", "")
        + "</ResultCollector>"
    )
    return arbol(el)


def grupo_hilos(nombre, hilos, subida, bucles=1, duracion=None, retraso=None, hijos=""):
    """hilos/subida/bucles/duracion/retraso pueden ser numeros o expresiones ${__P(...)}."""
    programador = duracion is not None
    el = (
        f'<ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="{escape(nombre)}" enabled="true">\n'
        + s("ThreadGroup.on_sample_error", "continue")
        + '<elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" '
        'testclass="LoopController" testname="Controlador de bucle" enabled="true">'
        + b("LoopController.continue_forever", False) + s("LoopController.loops", bucles)
        + "</elementProp>\n"
        + s("ThreadGroup.num_threads", hilos)
        + s("ThreadGroup.ramp_time", subida)
        + b("ThreadGroup.scheduler", programador)
        + s("ThreadGroup.duration", duracion if programador else "")
        + s("ThreadGroup.delay", retraso if retraso is not None else "")
        + b("ThreadGroup.same_user_on_next_iteration", True)
        + "</ThreadGroup>"
    )
    return arbol(el, hijos)


def controlador_si(nombre, expresion, hijos):
    el = (
        f'<IfController guiclass="IfControllerPanel" testclass="IfController" testname="{escape(nombre)}" enabled="true">\n'
        + s("IfController.condition", expresion) + b("IfController.evaluateAll", False)
        + b("IfController.useExpression", True)
        + "</IfController>"
    )
    return arbol(el, hijos)


def flujo_compra(timer=None, sufijo="", con_tarifas=True, debug=False):
    """GET tarifas, POST seleccion (+ extractor), POST pago (+ asercion)."""
    t = timer or ""
    partes = ""
    if con_tarifas:
        partes += peticion("Tarifas" + sufijo, "GET", "/api/tarifas", hijos=t)
    partes += peticion(
        "SeleccionTarifaYCantidad" + sufijo, "POST", "/api/seleccion",
        cuerpo='{"tarifa":"${tarifa}","cantidad":${cantidad}}',
        hijos=cabeceras() + extractor_reserva() + t)
    partes += debug_sampler(debug)
    partes += peticion(
        "Pago" + sufijo, "POST", "/api/pago", cuerpo='{"reserva":"${num_reserva}"}',
        hijos=cabeceras() + asercion_json("Asercion JSON: estado = APROBADO", "$.estado", "APROBADO"))
    return partes


# --------------------------------------------------------------------------
# Plan 1: Ticketmania.jmx (despliegue, escenario fijo)
# --------------------------------------------------------------------------
def plan_despliegue():
    timer = temporizador_aleatorio(500, 1000)
    # El temporizador va a nivel del grupo de hilos: aplica a todas las peticiones.
    hijos_gh = timer + flujo_compra()
    gh = grupo_hilos("Seleccion de tarifa y Pago", 200, 300, 1, hijos=hijos_gh)
    return plan("Ticketmania",
                valores_por_defecto() + csv("datos.csv", "tarifa,cantidad") + reporte_resumen() + gh)


# --------------------------------------------------------------------------
# Plan 2: Experimentacion.jmx (carga, estres, duracion, recursos)
#   propiedades: hilos, subida, duracion, ret_const, ret_rand, modo
# --------------------------------------------------------------------------
def plan_experimentacion():
    timer = temporizador_aleatorio("${__P(ret_const,500)}", "${__P(ret_rand,1000)}")
    flujo = controlador_si("Modo flujo completo", "${__jexl3('${__P(modo,flujo)}'=='flujo')}",
                           flujo_compra(timer=None, con_tarifas=True))
    solo_tarifas = controlador_si("Modo solo tarifas", "${__jexl3('${__P(modo,flujo)}'=='tarifas')}",
                                  peticion("Tarifas (solo lectura)", "GET", "/api/tarifas"))
    solo_sel = controlador_si("Modo solo seleccion", "${__jexl3('${__P(modo,flujo)}'=='seleccion')}",
                              peticion("Seleccion (crea reservas)", "POST", "/api/seleccion",
                                       cuerpo='{"tarifa":"${tarifa}","cantidad":${cantidad}}',
                                       hijos=cabeceras()))
    gh = grupo_hilos("Carga configurable", "${__P(hilos,20)}", "${__P(subida,10)}", -1,
                     duracion="${__P(duracion,60)}", hijos=timer + flujo + solo_tarifas + solo_sel)
    return plan("Experimentacion",
                valores_por_defecto() + csv("datos.csv", "tarifa,cantidad") + reporte_resumen() + gh)


# --------------------------------------------------------------------------
# Plan 3: Experimentacion_concurrencia.jmx (preguntas 7 y 8)
#   propiedades: hilos, subida, sync (1 = sincronizado, 0 = distribuido)
# --------------------------------------------------------------------------
def plan_concurrencia():
    sinc = controlador_si(
        "Disparo sincronizado", "${__jexl3(${__P(sync,1)}==1)}",
        peticion("Seleccion simultanea", "POST", "/api/seleccion",
                 cuerpo='{"tarifa":"${tarifa}","cantidad":${cantidad}}',
                 hijos=cabeceras() + extractor_reserva()
                 + asercion_json("Asercion JSON: reserva existe", "$.reserva", "", validar_valor=False)
                 + temporizador_sincronizado("${__P(hilos,500)}")))
    dist = controlador_si(
        "Llegada distribuida", "${__jexl3(${__P(sync,1)}==0)}",
        peticion("Seleccion distribuida", "POST", "/api/seleccion",
                 cuerpo='{"tarifa":"${tarifa}","cantidad":${cantidad}}',
                 hijos=cabeceras() + extractor_reserva()
                 + asercion_json("Asercion JSON: reserva existe", "$.reserva", "", validar_valor=False)))
    gh = grupo_hilos("Reservas al mismo tiempo", "${__P(hilos,500)}", "${__P(subida,0)}", 1, hijos=sinc + dist)
    return plan("Experimentacion_concurrencia",
                valores_por_defecto() + csv("datos.csv", "tarifa,cantidad") + reporte_resumen() + gh)


# --------------------------------------------------------------------------
# Plan 4: Experimentacion_validacion.jmx (pregunta 9)
#   CSV con total esperado = precio x cantidad; la asercion lo compara con $.total
# --------------------------------------------------------------------------
def plan_validacion():
    sel = peticion(
        "Seleccion con validacion de total", "POST", "/api/seleccion",
        cuerpo='{"tarifa":"${tarifa}","cantidad":${cantidad}}',
        hijos=cabeceras()
        + extractor_reserva()
        + asercion_json("Asercion JSON: total = precio x cantidad", "$.total", "${total_esperado}"))
    pago = peticion("Pago", "POST", "/api/pago", cuerpo='{"reserva":"${num_reserva}"}',
                    hijos=cabeceras() + asercion_json("Asercion JSON: estado = APROBADO", "$.estado", "APROBADO"))
    gh = grupo_hilos("Validacion de totales bajo carga", "${__P(hilos,200)}", "${__P(subida,10)}", "${__P(bucles,5)}",
                     hijos=sel + pago)
    return plan("Experimentacion_validacion",
                valores_por_defecto() + csv("${__P(csv,datos_validacion.csv)}", "tarifa,cantidad,total_esperado") + reporte_resumen() + gh)


def escribir(ruta, contenido):
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenido)
    print("escrito", ruta)


if __name__ == "__main__":
    escribir("pruebas/jmeter/Ticketmania.jmx", plan_despliegue())
    escribir("pruebas/experimentacion/Experimentacion.jmx", plan_experimentacion())
    escribir("pruebas/experimentacion/Experimentacion_concurrencia.jmx", plan_concurrencia())
    escribir("pruebas/experimentacion/Experimentacion_validacion.jmx", plan_validacion())
