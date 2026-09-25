"""Envío diario de recordatorios sin cron ni Programador de tareas.

Cuando la aplicación se arranca con `python servir.py`, un hilo comprueba cada
10 minutos si ya se han enviado los recordatorios de hoy. Si no se han enviado
y ya es la hora configurada (RECORDATORIO_HORA), los envía. Si el ordenador
estaba apagado a esa hora, se envían en cuanto vuelva a arrancar.
"""
import threading
import time
from datetime import datetime
from pathlib import Path

from .recordatorios import enviar_recordatorios

INTERVALO_SEGUNDOS = 600


def comprobar(app, ahora=None):
    """Envía los recordatorios si toca. Devuelve el resumen o None si no tocaba."""
    ahora = ahora or datetime.now()
    marca = Path(app.instance_path) / "ultimo_envio_recordatorios.txt"
    hoy = ahora.date().isoformat()
    if ahora.hour < app.config["RECORDATORIO_HORA"]:
        return None
    if marca.exists() and marca.read_text(encoding="utf-8").strip() == hoy:
        return None
    with app.app_context():
        resumen = enviar_recordatorios(ahora.date())
    marca.write_text(hoy, encoding="utf-8")
    app.logger.info("Recordatorios del %s enviados: %s", hoy, resumen or "ninguno")
    return resumen


def iniciar(app):
    def bucle():
        while True:
            try:
                comprobar(app)
            except Exception:  # nunca debe tumbar el servidor
                app.logger.exception("Fallo al enviar los recordatorios")
            time.sleep(INTERVALO_SEGUNDOS)

    threading.Thread(target=bucle, name="recordatorios", daemon=True).start()
