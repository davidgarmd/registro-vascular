"""Recordatorios de seguimiento por correo electrónico.

Se ejecuta una vez al día (cron o Programador de tareas de Windows):

    flask --app registro enviar-recordatorios

Cada cirujano recibe UN correo con sus seguimientos vencidos. Un seguimiento se
vuelve a recordar cada RECORDATORIO_REPETIR_DIAS días hasta completarse, con un
máximo de RECORDATORIO_MAX avisos. Los correos solo llevan el código del
paciente, el hito y un enlace: ningún dato clínico ni el NHC.
"""
import smtplib
from collections import defaultdict
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

from flask import current_app

from .db import auditar, get_db
from .formularios import ETIQUETA_HITO


def seguimientos_a_recordar(hoy):
    cfg = current_app.config
    limite = (hoy - timedelta(days=cfg["RECORDATORIO_REPETIR_DIAS"])).isoformat()
    return get_db().execute(
        """SELECT s.id, s.hito, s.fecha_prevista, s.recordatorios_enviados, pa.codigo,
                  u.id AS cirujano_id, u.nombre AS cirujano, u.email
           FROM seguimientos s
           JOIN procedimientos p ON p.id = s.procedimiento_id
           JOIN pacientes pa ON pa.id = p.paciente_id
           JOIN usuarios u ON u.id = p.cirujano_id
           WHERE s.estado = 'pendiente'
             AND s.fecha_prevista <= ?
             AND u.activo = 1
             AND s.recordatorios_enviados < ?
             AND (s.ultimo_recordatorio IS NULL OR date(s.ultimo_recordatorio) <= ?)
           ORDER BY u.id, s.fecha_prevista""",
        (hoy.isoformat(), cfg["RECORDATORIO_MAX"], limite),
    ).fetchall()


def componer_correo(nombre, email, filas):
    base = current_app.config["BASE_URL"].rstrip("/")
    n = len(filas)
    msg = EmailMessage()
    msg["Subject"] = f"[Registro vascular] {n} seguimiento{'s' if n != 1 else ''} pendiente{'s' if n != 1 else ''}"
    msg["From"] = current_app.config["MAIL_FROM"]
    msg["To"] = email
    lineas = [
        f"Hola, {nombre}:",
        "",
        "Tienes estos seguimientos pendientes de registrar:",
        "",
    ]
    for f in filas:
        lineas.append(
            f"  - {f['codigo']} · seguimiento a {ETIQUETA_HITO[f['hito']]} "
            f"(previsto el {f['fecha_prevista']})\n    {base}/seguimientos/{f['id']}"
        )
    lineas += [
        "",
        f"Ver todos tus pendientes: {base}/seguimientos?mios=1",
        "",
        "Si un seguimiento no se puede hacer (paciente perdido, trasladado…), márcalo como",
        "«no realizable» en la aplicación para dejar de recibir este aviso.",
        "",
        "Este correo no contiene datos clínicos. No respondas a este mensaje.",
    ]
    msg.set_content("\n".join(lineas))
    return msg


def enviar(msg):
    cfg = current_app.config
    if not cfg.get("MAIL_SERVER"):
        # Modo prueba: los correos se guardan como ficheros .eml en instance/outbox.
        carpeta = Path(cfg["OUTBOX"])
        carpeta.mkdir(parents=True, exist_ok=True)
        nombre = f"{datetime.now():%Y%m%d-%H%M%S-%f}-{msg['To'].replace('@', '_at_')}.eml"
        (carpeta / nombre).write_bytes(bytes(msg))
        return
    clase = smtplib.SMTP_SSL if cfg.get("MAIL_USE_SSL") else smtplib.SMTP
    with clase(cfg["MAIL_SERVER"], cfg["MAIL_PORT"], timeout=30) as smtp:
        if cfg.get("MAIL_USE_TLS") and not cfg.get("MAIL_USE_SSL"):
            smtp.starttls()
        if cfg.get("MAIL_USERNAME"):
            smtp.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
        smtp.send_message(msg)


def enviar_recordatorios(hoy=None):
    """Envía los recordatorios del día. Devuelve {email: nº de seguimientos}."""
    hoy = hoy or date.today()
    por_cirujano = defaultdict(list)
    for fila in seguimientos_a_recordar(hoy):
        por_cirujano[(fila["cirujano_id"], fila["cirujano"], fila["email"])].append(fila)

    db = get_db()
    resumen = {}
    for (cirujano_id, nombre, email), filas in por_cirujano.items():
        try:
            enviar(componer_correo(nombre, email, filas))
        except Exception as exc:  # un fallo con un cirujano no debe bloquear al resto
            current_app.logger.error("No se pudo enviar el recordatorio a %s: %s", email, exc)
            auditar("error_recordatorio", "usuario", cirujano_id, str(exc), usuario_id=None)
            db.commit()
            continue
        db.executemany(
            """UPDATE seguimientos SET recordatorios_enviados = recordatorios_enviados + 1,
               ultimo_recordatorio = ? WHERE id = ?""",
            [(hoy.isoformat(), f["id"]) for f in filas],
        )
        auditar("recordatorio", "usuario", cirujano_id, f"{len(filas)} seguimientos", usuario_id=None)
        db.commit()
        resumen[email] = len(filas)
    return resumen
