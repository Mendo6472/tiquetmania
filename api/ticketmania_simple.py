#!/usr/bin/env python3
"""API simple de Tiquetmania para el taller de JMeter.

Endpoints:
  GET  /api/salud       -> {"estado": "OK"}
  GET  /api/tarifas     -> lista de tarifas y precios
  POST /api/seleccion   -> {"tarifa": "general", "cantidad": 2} crea una reserva
  POST /api/pago        -> {"reserva": "<id>"} paga y consume la reserva

Reglas: sin topes de capacidad, datos en memoria, el pago siempre se aprueba,
y pagar la misma reserva dos veces responde 404.

Uso: python ticketmania_simple.py [--puerto 8080]
"""
import argparse
import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TARIFAS = {
    "general": 80000,
    "occidental": 120000,
    "preferencial": 180000,
    "vip": 350000,
}

RESERVAS = {}
BLOQUEO = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = "TicketManiaSimple"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass  # sin log por peticion para no afectar la medicion

    def _responder(self, codigo, cuerpo):
        datos = json.dumps(cuerpo).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _leer_json(self):
        largo = int(self.headers.get("Content-Length") or 0)
        crudo = self.rfile.read(largo) if largo else b""
        try:
            return json.loads(crudo.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return None

    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta == "/api/salud":
            self._responder(200, {"estado": "OK"})
        elif ruta == "/api/tarifas":
            self._responder(200, {"tarifas": [{"tarifa": k, "precio": v} for k, v in TARIFAS.items()]})
        else:
            self._responder(404, {"error": "No encontrado"})

    def do_POST(self):
        ruta = self.path.split("?")[0]
        datos = self._leer_json()
        if datos is None:
            self._responder(400, {"error": "JSON invalido"})
            return
        if ruta == "/api/seleccion":
            tarifa = datos.get("tarifa")
            cantidad = datos.get("cantidad")
            if tarifa not in TARIFAS:
                self._responder(400, {"error": "Tarifa invalida"})
                return
            if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
                self._responder(400, {"error": "Cantidad invalida"})
                return
            reserva = uuid.uuid4().hex
            total = TARIFAS[tarifa] * cantidad
            with BLOQUEO:
                RESERVAS[reserva] = {"tarifa": tarifa, "cantidad": cantidad, "total": total}
            self._responder(200, {"reserva": reserva, "tarifa": tarifa, "cantidad": cantidad,
                                  "precio_unitario": TARIFAS[tarifa], "total": total})
        elif ruta == "/api/pago":
            reserva = datos.get("reserva")
            with BLOQUEO:
                info = RESERVAS.pop(reserva, None)
            if info is None:
                self._responder(404, {"error": "Reserva no encontrada"})
                return
            self._responder(200, {"estado": "APROBADO", "reserva": reserva, "total": info["total"]})
        else:
            self._responder(404, {"error": "No encontrado"})


class Servidor(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 1024


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--puerto", type=int, default=8080)
    args = parser.parse_args()
    servidor = Servidor(("127.0.0.1", args.puerto), Handler)
    print(f"TicketManiaSimple escuchando en http://127.0.0.1:{args.puerto}", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
