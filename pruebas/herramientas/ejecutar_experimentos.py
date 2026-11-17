#!/usr/bin/env python3
"""Ejecuta los escenarios de experimentacion en local, uno por uno.

Para cada corrida: levanta una API limpia (los datos estan en memoria), mide
CPU y memoria del equipo cada segundo, ejecuta JMeter en modo no-GUI y genera
el reporte HTML. Requiere psutil (pip install psutil).

Uso (desde la raiz del repo):
  python pruebas/herramientas/ejecutar_experimentos.py [id_escenario ...]
Variables: JMETER_HOME (carpeta de apache-jmeter-5.6.3), REPS (repeticiones, 2).
"""
import csv
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime

import psutil

RAIZ = os.getcwd()
EXP = os.path.join(RAIZ, "pruebas", "experimentacion")
SALIDA = os.path.join(EXP, "resultados")
JMETER_HOME = os.environ.get("JMETER_HOME", os.path.expanduser("~/Tools/apache-jmeter-5.6.3"))
JMETER = os.path.join(JMETER_HOME, "bin", "jmeter.bat" if os.name == "nt" else "jmeter")
REPS = int(os.environ.get("REPS", "2"))
ETIQUETA = os.environ.get("ETIQUETA", "")  # sufijo de carpeta, para repetir una corrida sin pisar la anterior

GEN = "Experimentacion.jmx"
CON = "Experimentacion_concurrencia.jmx"
VAL = "Experimentacion_validacion.jmx"

# id: (pregunta, jmx, propiedades, repeticiones)
ESCENARIOS = {
    "q1_20u":        ("P1", GEN, dict(hilos=20, subida=10, duracion=60, modo="flujo"), REPS),
    "q1_500u":       ("P1", GEN, dict(hilos=500, subida=10, duracion=60, modo="flujo"), REPS),
    "q2_subida1":    ("P2", GEN, dict(hilos=100, subida=1, duracion=120, modo="flujo"), REPS),
    "q2_subida60":   ("P2", GEN, dict(hilos=100, subida=60, duracion=120, modo="flujo"), REPS),
    "q3_con_temp":   ("P3", GEN, dict(hilos=100, subida=10, duracion=60, modo="flujo"), REPS),
    "q3_sin_temp":   ("P3", GEN, dict(hilos=100, subida=10, duracion=60, modo="flujo", ret_const=0, ret_rand=0), REPS),
    "q4_50":         ("P4", GEN, dict(hilos=50, subida=10, duracion=60, modo="flujo", ret_const=0, ret_rand=0), REPS),
    "q4_100":        ("P4", GEN, dict(hilos=100, subida=10, duracion=60, modo="flujo", ret_const=0, ret_rand=0), REPS),
    "q4_250":        ("P4", GEN, dict(hilos=250, subida=10, duracion=60, modo="flujo", ret_const=0, ret_rand=0), REPS),
    "q4_500":        ("P4", GEN, dict(hilos=500, subida=10, duracion=60, modo="flujo", ret_const=0, ret_rand=0), REPS),
    "q5_1min":       ("P5", GEN, dict(hilos=200, subida=30, duracion=60, modo="flujo"), REPS),
    "q5_10min":      ("P5", GEN, dict(hilos=200, subida=30, duracion=600, modo="flujo"), 1),
    "q6_tarifas":    ("P6", GEN, dict(hilos=100, subida=10, duracion=60, modo="tarifas", ret_const=0, ret_rand=0), REPS),
    "q6_seleccion":  ("P6", GEN, dict(hilos=100, subida=10, duracion=60, modo="seleccion", ret_const=0, ret_rand=0), REPS),
    "q7_sync500":    ("P7-8", CON, dict(hilos=500, subida=0, sync=1, sample_variables="num_reserva"), REPS),
    "q8_distribuido": ("P8", CON, dict(hilos=500, subida=30, sync=0, sample_variables="num_reserva"), REPS),
    "q9_validacion": ("P9", VAL, dict(hilos=200, subida=10, bucles=5, csv="datos_validacion.csv"), REPS),
    "q9_control_error": ("P9", VAL, dict(hilos=200, subida=10, bucles=5, csv="datos_validacion_error.csv"), 1),
}


class Monitor(threading.Thread):
    """Mide CPU y memoria del equipo completo y de la API cada segundo (equivalente a PerfMon)."""

    def __init__(self, ruta, pid_api):
        super().__init__(daemon=True)
        self.ruta, self.pid_api, self.parar = ruta, pid_api, threading.Event()

    def run(self):
        raiz = psutil.Process(self.pid_api)

        def arbol():
            # En Windows el python de un venv es un lanzador: la API real es un proceso hijo.
            return [raiz] + raiz.children(recursive=True)

        for p in arbol():
            p.cpu_percent(None)
        psutil.cpu_percent(None)
        t0 = time.time()
        with open(self.ruta, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["segundo", "cpu_total_pct", "mem_usada_pct", "mem_usada_mb", "cpu_api_pct", "mem_api_mb", "mem_jmeter_mb"])
            while not self.parar.is_set():
                time.sleep(1)
                try:
                    vm = psutil.virtual_memory()
                    jm = 0.0
                    for p in psutil.process_iter(["name", "cmdline"]):
                        try:
                            if p.info["name"] and "java" in p.info["name"].lower() and any(
                                    "ApacheJMeter" in (c or "") for c in (p.info["cmdline"] or [])):
                                jm += p.memory_info().rss / 2**20
                        except (psutil.Error, TypeError):
                            pass
                    procs = arbol()
                    w.writerow([round(time.time() - t0), psutil.cpu_percent(None), vm.percent,
                                round((vm.total - vm.available) / 2**20), round(sum(p.cpu_percent(None) for p in procs), 1),
                                round(sum(p.memory_info().rss for p in procs) / 2**20, 1), round(jm)])
                    f.flush()
                except psutil.Error:
                    break


def esperar_api(puerto=8080, intentos=50):
    for _ in range(intentos):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/api/salud", timeout=1) as r:
                if b"OK" in r.read():
                    return True
        except OSError:
            time.sleep(0.2)
    return False


def entorno():
    java = subprocess.run(["java", "-version"], capture_output=True, text=True).stderr.splitlines()[0]
    return {
        "equipo": platform.node(), "so": platform.platform(), "procesador": platform.processor(),
        "nucleos_logicos": psutil.cpu_count(), "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
        "python": platform.python_version(), "java": java, "jmeter": "5.6.3",
        "api_y_jmeter_en_el_mismo_equipo": True,
    }


def correr(eid, rep):
    pregunta, jmx, props, _ = ESCENARIOS[eid]
    carpeta = os.path.join(SALIDA, eid, f"r{rep}{ETIQUETA}")
    shutil.rmtree(carpeta, ignore_errors=True)
    os.makedirs(carpeta)
    api = subprocess.Popen([sys.executable, os.path.join(RAIZ, "api", "ticketmania_simple.py")],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not esperar_api():
            raise RuntimeError("La API no respondio en /api/salud")
        mon = Monitor(os.path.join(carpeta, "monitor.csv"), api.pid)
        mon.start()
        cmd = [JMETER, "-n", "-t", jmx, "-l", os.path.join(carpeta, "resultados.jtl"),
               "-e", "-o", os.path.join(carpeta, "reporte")]
        cmd += [f"-J{k}={v}" for k, v in props.items()]
        inicio = datetime.now().isoformat(timespec="seconds")
        t0 = time.time()
        r = subprocess.run(cmd, cwd=EXP, capture_output=True, text=True)
        dur = time.time() - t0
        mon.parar.set()
        mon.join(3)
        with open(os.path.join(carpeta, "jmeter.log.txt"), "w", encoding="utf-8") as f:
            f.write(r.stdout[-6000:] + r.stderr[-2000:])
        meta = {"escenario": eid, "pregunta": pregunta, "plan": jmx, "propiedades": props, "repeticion": rep,
                "inicio": inicio, "duracion_s": round(dur, 1), "codigo_salida": r.returncode,
                "comando": " ".join(["jmeter"] + cmd[1:4] + [f"-J{k}={v}" for k, v in props.items()]),
                "entorno": entorno()}
        with open(os.path.join(carpeta, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        print(f"[{datetime.now():%H:%M:%S}] {eid} r{rep} listo en {dur:.0f}s (codigo {r.returncode})", flush=True)
    finally:
        for hijo in psutil.Process(api.pid).children(recursive=True) if api.poll() is None else []:
            hijo.kill()
        api.terminate()
        try:
            api.wait(5)
        except subprocess.TimeoutExpired:
            api.kill()
        time.sleep(2)


if __name__ == "__main__":
    ids = sys.argv[1:] or list(ESCENARIOS)
    for eid in ids:
        for rep in range(1, ESCENARIOS[eid][3] + 1):
            correr(eid, rep)
    print("TERMINADO", flush=True)
