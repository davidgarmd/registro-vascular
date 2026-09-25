import json
import sqlite3
from importlib import resources

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    schema = resources.files("registro").joinpath("schema.sql").read_text(encoding="utf-8")
    get_db().executescript(schema)


def auditar(accion, entidad=None, entidad_id=None, detalle=None, usuario_id=None):
    if usuario_id is None and g.get("usuario"):
        usuario_id = g.usuario["id"]
    get_db().execute(
        "INSERT INTO auditoria (usuario_id, accion, entidad, entidad_id, detalle) VALUES (?, ?, ?, ?, ?)",
        (usuario_id, accion, entidad, entidad_id, detalle),
    )


def cargar_json(texto):
    return json.loads(texto) if texto else {}


def init_app(app):
    app.teardown_appcontext(close_db)
