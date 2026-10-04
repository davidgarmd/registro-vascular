"""Acceso a datos: pacientes, procedimientos y seguimientos."""
import json
from datetime import date, datetime, timedelta

from flask import current_app

from .db import auditar, get_db
from .formularios import EXITUS_HOSPITALARIO, HITOS
from .seguridad import cifrar_nhc, nhc_hmac


def ahora():
    return datetime.now().isoformat(timespec="seconds")


# Pacientes --------------------------------------------------------------------

def buscar_paciente_por_nhc(nhc):
    return get_db().execute("SELECT * FROM pacientes WHERE nhc_hmac = ?", (nhc_hmac(nhc),)).fetchone()


def buscar_paciente_por_codigo(codigo):
    return get_db().execute(
        "SELECT * FROM pacientes WHERE codigo = ? COLLATE NOCASE", (codigo.strip(),)
    ).fetchone()


def obtener_paciente(paciente_id):
    return get_db().execute("SELECT * FROM pacientes WHERE id = ?", (paciente_id,)).fetchone()


def crear_paciente(nhc, sexo, usuario_id):
    db = get_db()
    cur = db.execute(
        "INSERT INTO pacientes (nhc_hmac, nhc_cifrado, sexo, creado_por) VALUES (?, ?, ?, ?)",
        (nhc_hmac(nhc), cifrar_nhc(nhc), sexo, usuario_id),
    )
    paciente_id = cur.lastrowid
    codigo = f"{current_app.config['PREFIJO_CODIGO']}-{paciente_id:05d}"
    db.execute("UPDATE pacientes SET codigo = ? WHERE id = ?", (codigo, paciente_id))
    auditar("crear", "paciente", paciente_id, usuario_id=usuario_id)
    db.commit()
    return paciente_id


# Procedimientos ---------------------------------------------------------------

def obtener_procedimiento(procedimiento_id):
    return get_db().execute(
        """SELECT p.*, pa.codigo, pa.sexo, u.nombre AS cirujano
           FROM procedimientos p
           JOIN pacientes pa ON pa.id = p.paciente_id
           JOIN usuarios u ON u.id = p.cirujano_id
           WHERE p.id = ?""",
        (procedimiento_id,),
    ).fetchone()


def procedimientos_de_paciente(paciente_id):
    return get_db().execute(
        """SELECT p.*, u.nombre AS cirujano FROM procedimientos p
           JOIN usuarios u ON u.id = p.cirujano_id
           WHERE p.paciente_id = ? ORDER BY p.fecha_cirugia DESC, p.id DESC""",
        (paciente_id,),
    ).fetchall()


def arbol_de_paciente(paciente_id):
    """Intervenciones del paciente con sus reintervenciones debajo: [(procedimiento, nivel), ...]."""
    procs = procedimientos_de_paciente(paciente_id)
    hijos = {}
    for p in procs:
        hijos.setdefault(p["procedimiento_origen_id"], []).append(p)
    for lista in hijos.values():
        lista.sort(key=lambda p: (p["fecha_cirugia"], p["id"]))
    raices = sorted(hijos.get(None, []), key=lambda p: (p["fecha_cirugia"], p["id"]), reverse=True)
    resultado = []

    def recorrer(p, nivel):
        resultado.append((p, nivel))
        for h in hijos.get(p["id"], []):
            recorrer(h, nivel + 1)

    for raiz in raices:
        recorrer(raiz, 0)
    return resultado


def reintervenciones_de(procedimiento_id):
    return get_db().execute(
        """SELECT p.*, u.nombre AS cirujano FROM procedimientos p
           JOIN usuarios u ON u.id = p.cirujano_id
           WHERE p.procedimiento_origen_id = ? ORDER BY p.fecha_cirugia""",
        (procedimiento_id,),
    ).fetchall()


def crear_procedimiento(paciente_id, tipo, fecha_cirugia, cirujano_id, datos, usuario_id,
                        origen_id=None, con_seguimiento=True):
    db = get_db()
    cur = db.execute(
        """INSERT INTO procedimientos (paciente_id, cirujano_id, tipo, fecha_cirugia, datos, creado_por,
                                       procedimiento_origen_id, con_seguimiento)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (paciente_id, cirujano_id, tipo, fecha_cirugia, json.dumps(datos, ensure_ascii=False), usuario_id,
         origen_id, int(con_seguimiento)),
    )
    procedimiento_id = cur.lastrowid
    base = date.fromisoformat(fecha_cirugia)
    for hito, dias, _ in (HITOS if con_seguimiento else []):
        db.execute(
            "INSERT INTO seguimientos (procedimiento_id, hito, dias, fecha_prevista) VALUES (?, ?, ?, ?)",
            (procedimiento_id, hito, dias, (base + timedelta(days=dias)).isoformat()),
        )
    auditar("crear", "procedimiento", procedimiento_id, tipo, usuario_id=usuario_id)
    if datos.get("destino_alta") == EXITUS_HOSPITALARIO:
        cerrar_seguimientos_por_fallecimiento(paciente_id, datos.get("fecha_exitus"), usuario_id)
    db.commit()
    return procedimiento_id


def actualizar_procedimiento(procedimiento_id, fecha_cirugia, cirujano_id, datos, usuario_id):
    db = get_db()
    db.execute(
        """UPDATE procedimientos SET fecha_cirugia = ?, cirujano_id = ?, datos = ?,
           modificado = ?, modificado_por = ? WHERE id = ?""",
        (fecha_cirugia, cirujano_id, json.dumps(datos, ensure_ascii=False), ahora(), usuario_id,
         procedimiento_id),
    )
    # Si cambia la fecha de cirugía se recalculan los seguimientos aún pendientes.
    db.execute(
        """UPDATE seguimientos SET fecha_prevista = date(?, '+' || dias || ' days')
           WHERE procedimiento_id = ? AND estado = 'pendiente'""",
        (fecha_cirugia, procedimiento_id),
    )
    auditar("editar", "procedimiento", procedimiento_id, usuario_id=usuario_id)
    if datos.get("destino_alta") == EXITUS_HOSPITALARIO:
        paciente_id = db.execute("SELECT paciente_id FROM procedimientos WHERE id = ?",
                                 (procedimiento_id,)).fetchone()["paciente_id"]
        cerrar_seguimientos_por_fallecimiento(paciente_id, datos.get("fecha_exitus"), usuario_id)
    db.commit()


# Seguimientos -----------------------------------------------------------------

def seguimientos_de_procedimiento(procedimiento_id):
    return get_db().execute(
        "SELECT * FROM seguimientos WHERE procedimiento_id = ? ORDER BY dias", (procedimiento_id,)
    ).fetchall()


def obtener_seguimiento(seguimiento_id):
    return get_db().execute(
        """SELECT s.*, p.tipo, p.fecha_cirugia, p.paciente_id, p.cirujano_id, pa.codigo
           FROM seguimientos s
           JOIN procedimientos p ON p.id = s.procedimiento_id
           JOIN pacientes pa ON pa.id = p.paciente_id
           WHERE s.id = ?""",
        (seguimiento_id,),
    ).fetchone()


def guardar_seguimiento(seguimiento_id, datos, usuario_id):
    db = get_db()
    db.execute(
        """UPDATE seguimientos SET estado = 'completado', datos = ?, motivo_no_realizable = NULL,
           completado = ?, completado_por = ? WHERE id = ?""",
        (json.dumps(datos, ensure_ascii=False), ahora(), usuario_id, seguimiento_id),
    )
    auditar("completar", "seguimiento", seguimiento_id, usuario_id=usuario_id)
    if datos.get("estado_vital") == "Fallecido":
        fila = db.execute(
            """SELECT p.paciente_id FROM seguimientos s JOIN procedimientos p ON p.id = s.procedimiento_id
               WHERE s.id = ?""", (seguimiento_id,)).fetchone()
        cerrar_seguimientos_por_fallecimiento(fila["paciente_id"], datos.get("fecha_fallecimiento"), usuario_id)
    db.commit()


def cerrar_seguimientos_por_fallecimiento(paciente_id, fecha, usuario_id):
    """Marca como no realizables los seguimientos pendientes de un paciente fallecido (sin más avisos)."""
    db = get_db()
    motivo = f"Paciente fallecido{' el ' + fecha if fecha else ''}"
    cur = db.execute(
        """UPDATE seguimientos SET estado = 'no_realizable', motivo_no_realizable = ?, completado = ?,
           completado_por = ?
           WHERE estado = 'pendiente'
             AND procedimiento_id IN (SELECT id FROM procedimientos WHERE paciente_id = ?)""",
        (motivo, ahora(), usuario_id, paciente_id),
    )
    if cur.rowcount:
        auditar("cerrar_por_fallecimiento", "paciente", paciente_id, f"{cur.rowcount} seguimientos",
                usuario_id=usuario_id)


def marcar_no_realizable(seguimiento_id, motivo, usuario_id):
    db = get_db()
    db.execute(
        """UPDATE seguimientos SET estado = 'no_realizable', motivo_no_realizable = ?,
           completado = ?, completado_por = ? WHERE id = ?""",
        (motivo, ahora(), usuario_id, seguimiento_id),
    )
    auditar("no_realizable", "seguimiento", seguimiento_id, motivo, usuario_id=usuario_id)
    db.commit()


def reabrir_seguimiento(seguimiento_id, usuario_id):
    db = get_db()
    db.execute(
        """UPDATE seguimientos SET estado = 'pendiente', completado = NULL, completado_por = NULL,
           motivo_no_realizable = NULL WHERE id = ?""",
        (seguimiento_id,),
    )
    auditar("reabrir", "seguimiento", seguimiento_id, usuario_id=usuario_id)
    db.commit()


def seguimientos_pendientes(hasta=None, cirujano_id=None):
    """Seguimientos pendientes con fecha prevista <= `hasta` (por defecto, todos)."""
    sql = """SELECT s.*, p.tipo, p.fecha_cirugia, p.cirujano_id, pa.codigo, pa.id AS paciente_id,
                    u.nombre AS cirujano
             FROM seguimientos s
             JOIN procedimientos p ON p.id = s.procedimiento_id
             JOIN pacientes pa ON pa.id = p.paciente_id
             JOIN usuarios u ON u.id = p.cirujano_id
             WHERE s.estado = 'pendiente'"""
    params = []
    if hasta is not None:
        sql += " AND s.fecha_prevista <= ?"
        params.append(hasta.isoformat())
    if cirujano_id is not None:
        sql += " AND p.cirujano_id = ?"
        params.append(cirujano_id)
    sql += " ORDER BY s.fecha_prevista"
    return get_db().execute(sql, params).fetchall()


# Usuarios ---------------------------------------------------------------------

def usuarios_activos():
    return get_db().execute("SELECT * FROM usuarios WHERE activo = 1 ORDER BY nombre").fetchall()
