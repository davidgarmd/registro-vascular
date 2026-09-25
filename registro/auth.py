import functools
import secrets

from flask import (Blueprint, abort, flash, g, redirect, render_template, request, session,
                   url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import auditar, get_db

bp = Blueprint("auth", __name__)

LONGITUD_MINIMA = 10


def login_requerido(vista):
    @functools.wraps(vista)
    def envoltura(**kwargs):
        if g.usuario is None:
            return redirect(url_for("auth.login", next=request.path))
        return vista(**kwargs)
    return envoltura


def admin_requerido(vista):
    @functools.wraps(vista)
    @login_requerido
    def envoltura(**kwargs):
        if not g.usuario["es_admin"]:
            abort(403)
        return vista(**kwargs)
    return envoltura


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


@bp.before_app_request
def cargar_usuario():
    usuario_id = session.get("usuario_id")
    g.usuario = None
    if usuario_id is not None:
        g.usuario = get_db().execute(
            "SELECT * FROM usuarios WHERE id = ? AND activo = 1", (usuario_id,)
        ).fetchone()
        if g.usuario is None:
            session.clear()
    if request.method == "POST":
        enviado = request.form.get("csrf_token", "")
        esperado = session.get("csrf")
        if not esperado or not secrets.compare_digest(enviado, esperado):
            abort(400, "Token de seguridad no válido. Recarga la página.")


def crear_usuario(nombre, email, password, es_admin=False):
    db = get_db()
    cur = db.execute(
        "INSERT INTO usuarios (nombre, email, password_hash, es_admin) VALUES (?, ?, ?, ?)",
        (nombre.strip(), email.strip().lower(), generate_password_hash(password), int(es_admin)),
    )
    db.commit()
    return cur.lastrowid


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        usuario = get_db().execute(
            "SELECT * FROM usuarios WHERE email = ? AND activo = 1", (email,)
        ).fetchone()
        if usuario and check_password_hash(usuario["password_hash"], request.form.get("password", "")):
            session.clear()
            session.permanent = True
            session["usuario_id"] = usuario["id"]
            auditar("login", "usuario", usuario["id"], usuario_id=usuario["id"])
            get_db().commit()
            destino = request.args.get("next", "")
            if not destino.startswith("/") or destino.startswith("//"):
                destino = url_for("main.inicio")
            return redirect(destino)
        auditar("login_fallido", detalle=email, usuario_id=None)
        get_db().commit()
        flash("Correo o contraseña incorrectos.", "error")
    return render_template("login.html")


@bp.route("/logout", methods=("POST",))
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@bp.route("/perfil", methods=("GET", "POST"))
@login_requerido
def perfil():
    if request.method == "POST":
        actual = request.form.get("actual", "")
        nueva = request.form.get("nueva", "")
        if not check_password_hash(g.usuario["password_hash"], actual):
            flash("La contraseña actual no es correcta.", "error")
        elif len(nueva) < LONGITUD_MINIMA:
            flash(f"La nueva contraseña debe tener al menos {LONGITUD_MINIMA} caracteres.", "error")
        elif nueva != request.form.get("repetir", ""):
            flash("Las contraseñas no coinciden.", "error")
        else:
            db = get_db()
            db.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?",
                       (generate_password_hash(nueva), g.usuario["id"]))
            auditar("cambiar_password", "usuario", g.usuario["id"])
            db.commit()
            flash("Contraseña actualizada.", "ok")
            return redirect(url_for("main.inicio"))
    return render_template("perfil.html")


@bp.route("/usuarios", methods=("GET", "POST"))
@admin_requerido
def usuarios():
    db = get_db()
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not nombre or "@" not in email:
            flash("Nombre y correo son obligatorios.", "error")
        elif len(password) < LONGITUD_MINIMA:
            flash(f"La contraseña debe tener al menos {LONGITUD_MINIMA} caracteres.", "error")
        elif db.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone():
            flash("Ya existe un usuario con ese correo.", "error")
        else:
            nuevo = crear_usuario(nombre, email, password, bool(request.form.get("es_admin")))
            auditar("crear", "usuario", nuevo)
            db.commit()
            flash(f"Usuario {email} creado. Comunícale la contraseña por un canal seguro.", "ok")
            return redirect(url_for("auth.usuarios"))
    lista = db.execute("SELECT * FROM usuarios ORDER BY activo DESC, nombre").fetchall()
    return render_template("usuarios.html", usuarios=lista, minimo=LONGITUD_MINIMA)


@bp.route("/usuarios/<int:usuario_id>/activo", methods=("POST",))
@admin_requerido
def alternar_activo(usuario_id):
    if usuario_id == g.usuario["id"]:
        flash("No puedes desactivarte a ti mismo.", "error")
        return redirect(url_for("auth.usuarios"))
    db = get_db()
    db.execute("UPDATE usuarios SET activo = 1 - activo WHERE id = ?", (usuario_id,))
    auditar("alternar_activo", "usuario", usuario_id)
    db.commit()
    return redirect(url_for("auth.usuarios"))


@bp.route("/usuarios/<int:usuario_id>/password", methods=("POST",))
@admin_requerido
def restablecer_password(usuario_id):
    password = request.form.get("password", "")
    if len(password) < LONGITUD_MINIMA:
        flash(f"La contraseña debe tener al menos {LONGITUD_MINIMA} caracteres.", "error")
    else:
        db = get_db()
        db.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?",
                   (generate_password_hash(password), usuario_id))
        auditar("restablecer_password", "usuario", usuario_id)
        db.commit()
        flash("Contraseña restablecida.", "ok")
    return redirect(url_for("auth.usuarios"))
