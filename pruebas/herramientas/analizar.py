#!/usr/bin/env python3
"""Lee los .jtl y el monitoreo de cada corrida y arma resumen.json y las graficas.

Uso (desde la raiz del repo): python pruebas/herramientas/analizar.py
Requiere matplotlib.
"""
import csv
import glob
import json
import os
import statistics
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = os.getcwd()
RES = os.path.join(RAIZ, "pruebas", "experimentacion", "resultados")
IMG = os.path.join(RAIZ, "entrega", "img")
os.makedirs(IMG, exist_ok=True)


def p95(v):
    v = sorted(v)
    return v[min(len(v) - 1, int(round(0.95 * len(v) + 0.5)) - 1)] if v else 0


def estadisticas(filas):
    el = [int(f["elapsed"]) for f in filas]
    ini = min(int(f["timeStamp"]) for f in filas)
    fin = max(int(f["timeStamp"]) + int(f["elapsed"]) for f in filas)
    seg = max((fin - ini) / 1000, 0.001)
    err = sum(1 for f in filas if f["success"].strip().lower() != "true")
    return {"muestras": len(filas), "media_ms": round(statistics.mean(el), 1), "mediana_ms": statistics.median(el),
            "p95_ms": p95(el), "max_ms": max(el), "error_pct": round(100 * err / len(filas), 2),
            "errores": err, "rendimiento_s": round(len(filas) / seg, 1), "duracion_s": round(seg, 1)}


def cargar_corrida(carpeta):
    with open(os.path.join(carpeta, "meta.json"), encoding="utf-8") as f:
        meta = json.load(f)
    with open(os.path.join(carpeta, "resultados.jtl"), newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    por_etiqueta = defaultdict(list)
    for fila in filas:
        por_etiqueta[fila["label"]].append(fila)
    r = {"meta": meta, "total": estadisticas(filas),
         "etiquetas": {k: estadisticas(v) for k, v in por_etiqueta.items()}}
    # Rendimiento por segundo y tiempo medio por minuto
    t0 = min(int(f["timeStamp"]) for f in filas)
    por_s, por_min = defaultdict(int), defaultdict(list)
    for fila in filas:
        s = (int(fila["timeStamp"]) - t0) // 1000
        por_s[s] += 1
        por_min[s // 60].append(int(fila["elapsed"]))
    r["rendimiento_por_segundo"] = [por_s.get(i, 0) for i in range(max(por_s) + 1)]
    r["media_por_minuto"] = [round(statistics.mean(por_min[m]), 1) for m in sorted(por_min)]
    r["p95_por_minuto"] = [p95(por_min[m]) for m in sorted(por_min)]
    if "num_reserva" in filas[0]:
        ids = [f["num_reserva"] for f in filas]
        r["reservas"] = {"respuestas": len(ids), "unicas": len(set(ids)), "sin_valor": sum(1 for i in ids if i in ("", "num_reserva_not_found"))}
        inicios = [int(f["timeStamp"]) for f in filas]
        r["dispersion_inicio_ms"] = max(inicios) - min(inicios)
    mon = os.path.join(carpeta, "monitor.csv")
    if os.path.exists(mon):
        with open(mon, newline="") as f:
            m = list(csv.DictReader(f))
        if m:
            cpu = [float(x["cpu_total_pct"]) for x in m]
            mem = [float(x["mem_usada_mb"]) for x in m]
            r["monitor"] = {
                "cpu_media_pct": round(statistics.mean(cpu), 1), "cpu_max_pct": max(cpu),
                "cpu_api_max_pct": max(float(x["cpu_api_pct"]) for x in m),
                "mem_inicio_mb": mem[0], "mem_fin_mb": mem[-1], "mem_max_mb": max(mem),
                "mem_usada_max_pct": max(float(x["mem_usada_pct"]) for x in m),
                "mem_api_max_mb": max(float(x["mem_api_mb"]) for x in m),
                "mem_jmeter_max_mb": max(float(x["mem_jmeter_mb"]) for x in m),
                "serie_cpu": cpu, "serie_mem_mb": mem,
                "serie_mem_jmeter_mb": [float(x["mem_jmeter_mb"]) for x in m],
                "serie_mem_api_mb": [float(x["mem_api_mb"]) for x in m],
            }
    return r


def main():
    datos = defaultdict(list)
    for carpeta in sorted(glob.glob(os.path.join(RES, "*", "r*"))):
        if not os.path.exists(os.path.join(carpeta, "meta.json")):
            continue
        r = cargar_corrida(carpeta)
        datos[r["meta"]["escenario"]].append(r)
    with open(os.path.join(RES, "resumen.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=1, ensure_ascii=False)

    def media(eid, clave, sub=None):
        vals = []
        for r in datos[eid]:
            v = r["total"][clave] if sub is None else r["etiquetas"][sub][clave]
            vals.append(v)
        return round(statistics.mean(vals), 1) if vals else 0

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    C1, C2, C3 = "#1f6feb", "#d1495b", "#2a9d8f"

    def barras(ids, etiquetas, titulo, archivo, colores=None):
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
        for a, (clave, nombre) in zip(ax, [("rendimiento_s", "Rendimiento (peticiones/s)"), ("media_ms", "Media (ms)")]):
            vals = [media(i, clave) for i in ids if i in datos]
            a.bar(etiquetas[:len(vals)], vals, color=colores or [C1, C2, C3, "#e9c46a"][:len(vals)])
            for x, v in enumerate(vals):
                a.text(x, v, f"{v}", ha="center", va="bottom", fontsize=9)
            a.set_title(nombre)
        fig.suptitle(titulo)
        fig.tight_layout()
        fig.savefig(os.path.join(IMG, archivo), dpi=130)
        plt.close(fig)

    if "q1_20u" in datos and "q1_500u" in datos:
        barras(["q1_20u", "q1_500u"], ["20 usuarios", "500 usuarios"], "Pregunta 1: 20 vs 500 usuarios", "q1.png")
    if "q3_con_temp" in datos and "q3_sin_temp" in datos:
        barras(["q3_con_temp", "q3_sin_temp"], ["Con temporizador", "Sin temporizador"], "Pregunta 3: con y sin temporizadores", "q3.png")
    if "q6_tarifas" in datos and "q6_seleccion" in datos:
        barras(["q6_tarifas", "q6_seleccion"], ["/api/tarifas", "/api/seleccion"], "Pregunta 6: costo por endpoint, misma carga", "q6.png")
    if "q8_distribuido" in datos and "q7_sync500" in datos:
        barras(["q7_sync500", "q8_distribuido"], ["Sincronizado", "Distribuido (30 s)"], "Pregunta 8: sincronizado vs distribuido", "q8.png")

    ids4 = [i for i in ["q4_50", "q4_100", "q4_250", "q4_500"] if i in datos]
    if ids4:
        us = [int(i.split("_")[1]) for i in ids4]
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
        ax[0].plot(us, [media(i, "rendimiento_s") for i in ids4], "o-", color=C1)
        ax[0].set_title("Rendimiento (peticiones/s)")
        ax[1].plot(us, [media(i, "media_ms") for i in ids4], "o-", color=C2, label="Media")
        ax[1].plot(us, [media(i, "p95_ms") for i in ids4], "s--", color=C3, label="p95")
        ax[1].set_title("Tiempo de respuesta (ms)")
        ax[1].legend()
        for a in ax:
            a.set_xlabel("Usuarios")
            a.set_xticks(us)
        fig.suptitle("Pregunta 4: escalones de usuarios, sin temporizadores")
        fig.tight_layout()
        fig.savefig(os.path.join(IMG, "q4.png"), dpi=130)
        plt.close(fig)

    if "q2_subida1" in datos and "q2_subida60" in datos:
        fig, ax = plt.subplots(figsize=(9, 3.4))
        for eid, nombre, col in [("q2_subida1", "Subida 1 s", C2), ("q2_subida60", "Subida 60 s", C1)]:
            serie = datos[eid][0]["rendimiento_por_segundo"]
            ax.plot(range(len(serie)), serie, color=col, label=nombre)
        ax.set_xlabel("Segundo de la prueba")
        ax.set_ylabel("Peticiones por segundo")
        ax.set_title("Pregunta 2: rendimiento por segundo con 100 usuarios")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(IMG, "q2.png"), dpi=130)
        plt.close(fig)

    if "q5_10min" in datos and "q5_1min" in datos:
        fig, ax = plt.subplots(figsize=(9, 3.4))
        r10 = datos["q5_10min"][0]
        ax.plot(range(1, len(r10["media_por_minuto"]) + 1), r10["media_por_minuto"], "o-", color=C1, label="Media por minuto")
        ax.plot(range(1, len(r10["p95_por_minuto"]) + 1), r10["p95_por_minuto"], "s--", color=C3, label="p95 por minuto")
        ax.set_xlabel("Minuto de la prueba de 10 minutos")
        ax.set_ylabel("ms")
        ax.set_title("Pregunta 5: tiempo de respuesta durante 10 minutos")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(IMG, "q5.png"), dpi=130)
        plt.close(fig)

    if "q9_validacion" in datos and "q9_control_error" in datos:
        fig, ax = plt.subplots(figsize=(6, 3.4))
        nombres = ["Totales correctos", "Control: 20 % del CSV con total mal"]
        vals = [datos["q9_validacion"][0]["total"]["errores"], datos["q9_control_error"][0]["total"]["errores"]]
        ax.bar(nombres, vals, color=[C3, C2])
        for x, v in enumerate(vals):
            ax.text(x, v, str(v), ha="center", va="bottom")
        ax.set_title("Pregunta 9: muestras fallidas por la asercion del total")
        fig.tight_layout()
        fig.savefig(os.path.join(IMG, "q9.png"), dpi=130)
        plt.close(fig)

    ids10 = [(i, n) for i, n in [("q1_20u", "20 usuarios"), ("q1_500u", "500 usuarios con temporizador"),
                                  ("q4_500", "500 usuarios sin temporizador")] if i in datos]
    if ids10:
        fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
        for (eid, nombre), col in zip(ids10, [C3, C1, C2]):
            m = datos[eid][0].get("monitor")
            if m:
                ax[0].plot(m["serie_cpu"], color=col, label=nombre)
                ax[1].plot(m["serie_mem_mb"], color=col, label=nombre)
        ax[0].set_title("CPU total del equipo (%)")
        ax[1].set_title("Memoria usada del equipo (MB)")
        for a in ax:
            a.set_xlabel("Segundo de la prueba")
        ax[0].set_ylim(0, 100)
        ax[0].legend(fontsize=8)
        fig.suptitle("Pregunta 10: CPU y memoria durante la prueba")
        fig.tight_layout()
        fig.savefig(os.path.join(IMG, "q10.png"), dpi=130)
        plt.close(fig)
    print("resumen y graficas listos:", sorted(datos))


if __name__ == "__main__":
    main()
