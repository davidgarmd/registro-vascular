import random
import secrets
from datetime import date, timedelta
from pathlib import Path

import click
from cryptography.fernet import Fernet
from flask import current_app
from flask.cli import with_appcontext

from . import modelos
from .auth import LONGITUD_MINIMA, crear_usuario
from .db import get_db, init_db
from .formularios import PROCEDIMIENTOS, campos, formulario_cirugia, formulario_seguimiento, visible
from .recordatorios import enviar_recordatorios

PLANTILLA_CONFIG = '''\
# Configuración local del registro. NO subir nunca este fichero a GitHub.
# Haz copia de seguridad: sin NHC_KEY los NHC guardados no pueden descifrarse.

SECRET_KEY = "{secret}"
NHC_KEY = "{nhc}"
HMAC_KEY = "{hmac}"

# Dirección con la que los cirujanos acceden a la aplicación (se usa en los enlaces de los correos).
BASE_URL = "http://localhost:5000"
PREFIJO_CODIGO = "RV"

# Correo saliente. Si MAIL_SERVER queda en None, los correos se guardan como
# ficheros .eml en instance/outbox (modo prueba).
MAIL_SERVER = None            # p. ej. "smtp.hospital.es"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_FROM = "registro-vascular@hospital.es"

RECORDATORIO_REPETIR_DIAS = 7  # volver a avisar cada N días mientras siga pendiente
RECORDATORIO_MAX = 4           # número máximo de avisos por seguimiento
RECORDATORIO_HORA = 8          # hora a partir de la cual servir.py envía los avisos del día

# Poner a True si se accede a través de Tailscale Serve o Cloudflare Tunnel (HTTPS).
DETRAS_DE_PROXY = False

# Activar si la aplicación se sirve por HTTPS (recomendado fuera de pruebas).
SESSION_COOKIE_SECURE = False
'''


@click.command("init")
@with_appcontext
def init_command():
    """Crea la configuración con claves nuevas (si no existe) y la base de datos."""
    ruta = Path(current_app.instance_path) / "config.py"
    if ruta.exists():
        click.echo(f"Ya existe {ruta}; se conservan sus claves.")
    else:
        ruta.write_text(PLANTILLA_CONFIG.format(
            secret=secrets.token_hex(32), nhc=Fernet.generate_key().decode(), hmac=secrets.token_hex(32),
        ), encoding="utf-8")
        ruta.chmod(0o600)
        click.echo(f"Configuración creada en {ruta}. Guarda una copia de seguridad en un lugar seguro.")
    current_app.config.from_pyfile(str(ruta))
    init_db()
    click.echo(f"Base de datos lista en {current_app.config['DATABASE']}.")


@click.command("crear-usuario")
@with_appcontext
@click.option("--nombre", prompt="Nombre (p. ej. Dra. García)")
@click.option("--email", prompt="Correo")
@click.option("--admin", is_flag=True, help="Da permisos de administración.")
@click.password_option("--password", prompt="Contraseña")
def crear_usuario_command(nombre, email, admin, password):
    """Crea un usuario (el primero debería ser administrador)."""
    if len(password) < LONGITUD_MINIMA:
        raise click.ClickException(f"La contraseña debe tener al menos {LONGITUD_MINIMA} caracteres.")
    crear_usuario(nombre, email, password, admin)
    click.echo(f"Usuario {email} creado{' como administrador' if admin else ''}.")


@click.command("enviar-recordatorios")
@with_appcontext
@click.option("--fecha", help="Simula otro día (AAAA-MM-DD). Útil para pruebas.")
def enviar_recordatorios_command(fecha):
    """Envía por correo los seguimientos vencidos a cada cirujano."""
    resumen = enviar_recordatorios(date.fromisoformat(fecha) if fecha else None)
    if not resumen:
        click.echo("Nada que enviar.")
    for email, n in resumen.items():
        click.echo(f"{email}: {n} seguimiento(s)")
    if not current_app.config.get("MAIL_SERVER") and resumen:
        click.echo(f"(Modo prueba: correos guardados en {current_app.config['OUTBOX']})")


def datos_aleatorios(secciones, rng):
    """Rellena un formulario con valores válidos al azar (solo para la demo)."""
    datos = {}
    for c in campos(secciones):
        if not visible(c, datos) or (not c["req"] and rng.random() < 0.3):
            continue
        tipo = c["tipo"]
        if tipo in ("select", "radio", "sino"):
            datos[c["nombre"]] = rng.choice(c["opciones"])
        elif tipo == "multi":
            datos[c["nombre"]] = rng.sample(c["opciones"], k=min(len(c["opciones"]), rng.randint(1, 2)))
        elif tipo == "numero":
            datos[c["nombre"]] = rng.randint(int(c.get("min", 0)), int(c.get("max", 100)))
        elif tipo == "fecha":
            datos[c["nombre"]] = date.today().isoformat()
        else:
            datos[c["nombre"]] = "Texto de ejemplo"
    return datos


@click.command("demo")
@with_appcontext
@click.option("--pacientes", default=25, show_default=True)
def demo_command(pacientes):
    """Carga usuarios y pacientes FICTICIOS para probar la aplicación."""
    db = get_db()
    if db.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0]:
        raise click.ClickException("La base de datos ya tiene pacientes; la demo solo se carga en una base vacía.")
    rng = random.Random(42)
    password = "demo-registro-2026"
    ids = []
    for nombre, email, admin in [("Admin Demo", "admin@demo.local", True),
                                 ("Dra. Demo Uno", "cirujana1@demo.local", False),
                                 ("Dr. Demo Dos", "cirujano2@demo.local", False)]:
        existente = db.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
        ids.append(existente["id"] if existente else crear_usuario(nombre, email, password, admin))
    tipos = list(PROCEDIMIENTOS)
    for i in range(pacientes):
        paciente_id = modelos.crear_paciente(f"DEMO{100000 + i}", rng.choice(["Hombre", "Mujer"]), ids[0])
        tipo = tipos[i % len(tipos)]
        fecha = date.today() - timedelta(days=rng.randint(0, 420))
        proc = modelos.crear_procedimiento(paciente_id, tipo, fecha.isoformat(), rng.choice(ids),
                                           datos_aleatorios(formulario_cirugia(tipo), rng), ids[0])
        for s in modelos.seguimientos_de_procedimiento(proc):
            if s["fecha_prevista"] <= date.today().isoformat() and rng.random() < 0.6:
                datos = datos_aleatorios(formulario_seguimiento(tipo), rng)
                datos["fecha_revision"] = s["fecha_prevista"]
                modelos.guardar_seguimiento(s["id"], datos, ids[0])
    click.echo(f"Demo cargada: {pacientes} pacientes ficticios.")
    click.echo(f"Usuarios: admin@demo.local, cirujana1@demo.local, cirujano2@demo.local · contraseña: {password}")


def init_app(app):
    for comando in (init_command, crear_usuario_command, enviar_recordatorios_command, demo_command):
        app.cli.add_command(comando)
