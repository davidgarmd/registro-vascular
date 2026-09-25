"""Registro de actividad quirúrgica vascular con seguimiento y recordatorios."""
import os
from datetime import timedelta

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, "registro.sqlite3"),
        OUTBOX=os.path.join(app.instance_path, "outbox"),
        PREFIJO_CODIGO="RV",
        BASE_URL="http://localhost:5000",
        MAIL_SERVER=None,
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USE_SSL=False,
        MAIL_USERNAME=None,
        MAIL_PASSWORD=None,
        MAIL_FROM="registro-vascular@localhost",
        RECORDATORIO_REPETIR_DIAS=7,
        RECORDATORIO_MAX=4,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    )
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
        app.config.from_prefixed_env("REGISTRO")  # p. ej. REGISTRO_MAIL_SERVER=smtp.hospital.es
    else:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    @app.before_request
    def comprobar_configuracion():
        if not app.config.get("SECRET_KEY") or not app.config.get("NHC_KEY"):
            return ("La aplicación no está inicializada. Ejecuta: flask --app registro init", 503)

    from . import auth, cli, db, vistas
    db.init_app(app)
    cli.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(vistas.bp)
    app.jinja_env.globals["csrf_token"] = auth.csrf_token
    return app
