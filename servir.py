"""Arranca el registro en este ordenador.

    python servir.py

Sirve la aplicación con waitress (apto para uso real, a diferencia de
`flask run`) y envía los recordatorios una vez al día sin necesidad de cron.
Por defecto solo escucha en este ordenador (127.0.0.1); el acceso remoto se
hace a través de Tailscale o de Cloudflare Tunnel (ver README).
"""
import argparse
import logging
import sys
from pathlib import Path

from waitress import serve

from registro import create_app
from registro.programador import iniciar


def main():
    parser = argparse.ArgumentParser(description="Servidor del registro vascular")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Interfaz de escucha (por defecto solo este ordenador)")
    parser.add_argument("--puerto", type=int, default=8080)
    parser.add_argument("--sin-recordatorios", action="store_true",
                        help="No enviar recordatorios automáticos desde este proceso")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = create_app()
    if not (Path(app.instance_path) / "config.py").exists():
        sys.exit("Falta la configuración. Ejecuta primero: flask --app registro init")
    if not args.sin_recordatorios:
        iniciar(app)
    print(f"Registro vascular en http://{args.host}:{args.puerto}  (Ctrl+C para parar)")
    serve(app, host=args.host, port=args.puerto, threads=8)


if __name__ == "__main__":
    main()
