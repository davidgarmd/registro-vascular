import csv
import io
from datetime import date, timedelta

from flask import (Blueprint, Response, abort, flash, g, redirect, render_template, request,
                   url_for)

from . import modelos
from .auth import admin_requerido, login_requerido
from .db import auditar, cargar_json, get_db
from .formularios import (ETIQUETA_HITO, PROCEDIMIENTOS, campos, formulario_cirugia,
                          formulario_seguimiento, procesar, valor_legible)
from .recordatorios import enviar_recordatorios
from .seguridad import descifrar_nhc

bp = Blueprint("main", __name__)

SEXOS = ["Hombre", "Mujer"]


@bp.app_context_processor
def utilidades():
    return {
        "PROCEDIMIENTOS": PROCEDIMIENTOS,
        "ETIQUETA_HITO": ETIQUETA_HITO,
        "hoy": date.today().isoformat(),
        "valor_legible": valor_legible,
    }


@bp.route("/")
@login_requerido
def inicio():
    hoy = date.today()
    mios_vencidos = modelos.seguimientos_pendientes(hasta=hoy, cirujano_id=g.usuario["id"])
    mios_proximos = [
        s for s in modelos.seguimientos_pendientes(hasta=hoy + timedelta(days=30), cirujano_id=g.usuario["id"])
        if s["fecha_prevista"] > hoy.isoformat()
    ]
    db = get_db()
    totales = {
        "pacientes": db.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0],
        "procedimientos": db.execute("SELECT COUNT(*) FROM procedimientos").fetchone()[0],
        "vencidos": len(modelos.seguimientos_pendientes(hasta=hoy)),
    }
    recientes = db.execute(
        """SELECT p.id, p.tipo, p.fecha_cirugia, pa.codigo, u.nombre AS cirujano
           FROM procedimientos p JOIN pacientes pa ON pa.id = p.paciente_id
           JOIN usuarios u ON u.id = p.cirujano_id
           ORDER BY p.creado DESC LIMIT 10"""
    ).fetchall()
    return render_template("inicio.html", vencidos=mios_vencidos, proximos=mios_proximos,
                           totales=totales, recientes=recientes)


@bp.route("/buscar")
@login_requerido
def buscar():
    q = request.args.get("q", "").strip()
    if not q:
        return redirect(url_for("main.inicio"))
    paciente = modelos.buscar_paciente_por_codigo(q) or modelos.buscar_paciente_por_nhc(q)
    if paciente:
        return redirect(url_for("main.paciente", paciente_id=paciente["id"]))
    flash("No hay ningún paciente con ese código o NHC. Puedes darlo de alta.", "aviso")
    return redirect(url_for("main.nuevo_paciente"))


# Pacientes --------------------------------------------------------------------

@bp.route("/pacientes")
@login_requerido
def pacientes():
    filas = get_db().execute(
        """SELECT pa.id, pa.codigo, pa.sexo, COUNT(p.id) AS n_proc, MAX(p.fecha_cirugia) AS ultima
           FROM pacientes pa LEFT JOIN procedimientos p ON p.paciente_id = pa.id
           GROUP BY pa.id ORDER BY pa.id DESC LIMIT 500"""
    ).fetchall()
    return render_template("pacientes.html", pacientes=filas)


@bp.route("/pacientes/nuevo", methods=("GET", "POST"))
@login_requerido
def nuevo_paciente():
    if request.method == "POST":
        nhc = request.form.get("nhc", "").strip()
        sexo = request.form.get("sexo", "")
        if not nhc:
            flash("El NHC es obligatorio.", "error")
        elif nhc != request.form.get("nhc2", "").strip():
            flash("Los dos NHC no coinciden. Revísalo.", "error")
        elif sexo not in SEXOS:
            flash("Indica el sexo.", "error")
        else:
            existente = modelos.buscar_paciente_por_nhc(nhc)
            if existente:
                flash(f"Ese NHC ya estaba registrado como {existente['codigo']}.", "aviso")
                return redirect(url_for("main.paciente", paciente_id=existente["id"]))
            paciente_id = modelos.crear_paciente(nhc, sexo, g.usuario["id"])
            flash("Paciente registrado. Ahora añade la intervención.", "ok")
            return redirect(url_for("main.nuevo_procedimiento", paciente_id=paciente_id))
    return render_template("paciente_nuevo.html", sexos=SEXOS)


@bp.route("/pacientes/<int:paciente_id>")
@login_requerido
def paciente(paciente_id):
    pac = modelos.obtener_paciente(paciente_id) or abort(404)
    procedimientos = [
        (p, modelos.seguimientos_de_procedimiento(p["id"]))
        for p in modelos.procedimientos_de_paciente(paciente_id)
    ]
    auditar("ver", "paciente", paciente_id)
    get_db().commit()
    return render_template("paciente.html", paciente=pac, nhc=descifrar_nhc(pac["nhc_cifrado"]),
                           procedimientos=procedimientos)


# Procedimientos ---------------------------------------------------------------

def _procesar_procedimiento(tipo):
    secciones = formulario_cirugia(tipo)
    datos, errores = procesar(secciones, request.form)
    fecha = request.form.get("fecha_cirugia", "")
    try:
        if date.fromisoformat(fecha) > date.today():
            errores["fecha_cirugia"] = "La fecha no puede ser futura."
    except ValueError:
        errores["fecha_cirugia"] = "Fecha obligatoria."
    cirujano_id = request.form.get("cirujano_id", type=int)
    if cirujano_id not in {u["id"] for u in modelos.usuarios_activos()}:
        errores["cirujano_id"] = "Elige el cirujano responsable."
    return secciones, datos, errores, fecha, cirujano_id


@bp.route("/pacientes/<int:paciente_id>/procedimientos/nuevo", methods=("GET", "POST"))
@login_requerido
def nuevo_procedimiento(paciente_id):
    pac = modelos.obtener_paciente(paciente_id) or abort(404)
    tipo = request.args.get("tipo")
    if tipo not in PROCEDIMIENTOS:
        return render_template("elegir_tipo.html", paciente=pac)
    secciones = formulario_cirugia(tipo)
    datos, errores = {}, {}
    fecha, cirujano_id = "", g.usuario["id"]
    if request.method == "POST":
        secciones, datos, errores, fecha, cirujano_id = _procesar_procedimiento(tipo)
        if not errores:
            nuevo = modelos.crear_procedimiento(paciente_id, tipo, fecha, cirujano_id, datos, g.usuario["id"])
            flash("Intervención guardada. Se han programado los seguimientos a 1, 3, 6 y 12 meses.", "ok")
            return redirect(url_for("main.procedimiento", procedimiento_id=nuevo))
        flash("Revisa los campos marcados.", "error")
    return render_template("procedimiento_form.html", paciente=pac, tipo=tipo, secciones=secciones,
                           datos=datos, errores=errores, fecha=fecha, cirujano_id=cirujano_id,
                           cirujanos=modelos.usuarios_activos(), editar=False)


@bp.route("/procedimientos/<int:procedimiento_id>")
@login_requerido
def procedimiento(procedimiento_id):
    proc = modelos.obtener_procedimiento(procedimiento_id) or abort(404)
    return render_template("procedimiento.html", proc=proc, datos=cargar_json(proc["datos"]),
                           secciones=formulario_cirugia(proc["tipo"]),
                           seguimientos=modelos.seguimientos_de_procedimiento(procedimiento_id))


@bp.route("/procedimientos/<int:procedimiento_id>/editar", methods=("GET", "POST"))
@login_requerido
def editar_procedimiento(procedimiento_id):
    proc = modelos.obtener_procedimiento(procedimiento_id) or abort(404)
    tipo = proc["tipo"]
    secciones = formulario_cirugia(tipo)
    datos, errores = cargar_json(proc["datos"]), {}
    fecha, cirujano_id = proc["fecha_cirugia"], proc["cirujano_id"]
    if request.method == "POST":
        secciones, datos, errores, fecha, cirujano_id = _procesar_procedimiento(tipo)
        if not errores:
            modelos.actualizar_procedimiento(procedimiento_id, fecha, cirujano_id, datos, g.usuario["id"])
            flash("Cambios guardados.", "ok")
            return redirect(url_for("main.procedimiento", procedimiento_id=procedimiento_id))
        flash("Revisa los campos marcados.", "error")
    return render_template("procedimiento_form.html", paciente=modelos.obtener_paciente(proc["paciente_id"]),
                           tipo=tipo, secciones=secciones, datos=datos, errores=errores, fecha=fecha,
                           cirujano_id=cirujano_id, cirujanos=modelos.usuarios_activos(), editar=True,
                           proc=proc)


# Seguimientos -----------------------------------------------------------------

@bp.route("/seguimientos")
@login_requerido
def seguimientos():
    mios = request.args.get("mios") == "1"
    solo_vencidos = request.args.get("vencidos", "1") == "1"
    filas = modelos.seguimientos_pendientes(
        hasta=date.today() if solo_vencidos else None,
        cirujano_id=g.usuario["id"] if mios else None,
    )
    return render_template("seguimientos.html", filas=filas, mios=mios, solo_vencidos=solo_vencidos)


@bp.route("/seguimientos/<int:seguimiento_id>", methods=("GET", "POST"))
@login_requerido
def seguimiento(seguimiento_id):
    seg = modelos.obtener_seguimiento(seguimiento_id) or abort(404)
    secciones = formulario_seguimiento(seg["tipo"])
    datos, errores = cargar_json(seg["datos"]), {}
    if request.method == "POST":
        accion = request.form.get("accion")
        if accion == "no_realizable":
            motivo = request.form.get("motivo", "").strip()
            if not motivo:
                flash("Indica el motivo por el que no se puede realizar.", "error")
            else:
                modelos.marcar_no_realizable(seguimiento_id, motivo, g.usuario["id"])
                flash("Seguimiento marcado como no realizable.", "ok")
                return redirect(url_for("main.procedimiento", procedimiento_id=seg["procedimiento_id"]))
        elif accion == "reabrir":
            modelos.reabrir_seguimiento(seguimiento_id, g.usuario["id"])
            flash("Seguimiento reabierto.", "ok")
            return redirect(url_for("main.seguimiento", seguimiento_id=seguimiento_id))
        else:
            datos, errores = procesar(secciones, request.form)
            if not errores:
                modelos.guardar_seguimiento(seguimiento_id, datos, g.usuario["id"])
                flash("Seguimiento guardado.", "ok")
                return redirect(url_for("main.procedimiento", procedimiento_id=seg["procedimiento_id"]))
            flash("Revisa los campos marcados.", "error")
    return render_template("seguimiento_form.html", seg=seg, secciones=secciones, datos=datos,
                           errores=errores)


# Administración ---------------------------------------------------------------

@bp.route("/admin/recordatorios", methods=("POST",))
@admin_requerido
def recordatorios_ahora():
    resumen = enviar_recordatorios()
    if resumen:
        detalle = ", ".join(f"{email} ({n})" for email, n in resumen.items())
        flash(f"Recordatorios enviados: {detalle}.", "ok")
    else:
        flash("No había recordatorios pendientes de enviar hoy.", "aviso")
    return redirect(url_for("main.inicio"))


@bp.route("/exportar")
@admin_requerido
def exportar():
    return render_template("exportar.html")


@bp.route("/exportar/<tipo>/<que>.csv")
@admin_requerido
def exportar_csv(tipo, que):
    if tipo not in PROCEDIMIENTOS or que not in ("procedimientos", "seguimientos"):
        abort(404)
    db = get_db()
    salida = io.StringIO()
    escritor = csv.writer(salida, delimiter=";")
    if que == "procedimientos":
        nombres = [c["nombre"] for c in campos(formulario_cirugia(tipo))]
        escritor.writerow(["codigo", "sexo", "procedimiento_id", "fecha_cirugia", "cirujano"] + nombres)
        filas = db.execute(
            """SELECT p.*, pa.codigo, pa.sexo, u.nombre AS cirujano FROM procedimientos p
               JOIN pacientes pa ON pa.id = p.paciente_id JOIN usuarios u ON u.id = p.cirujano_id
               WHERE p.tipo = ? ORDER BY p.fecha_cirugia""", (tipo,)).fetchall()
        for f in filas:
            d = cargar_json(f["datos"])
            escritor.writerow([f["codigo"], f["sexo"], f["id"], f["fecha_cirugia"], f["cirujano"]]
                              + [valor_legible(d.get(n)) for n in nombres])
    else:
        nombres = [c["nombre"] for c in campos(formulario_seguimiento(tipo))]
        escritor.writerow(["codigo", "procedimiento_id", "fecha_cirugia", "hito", "fecha_prevista",
                           "estado", "motivo_no_realizable"] + nombres)
        filas = db.execute(
            """SELECT s.*, p.fecha_cirugia, pa.codigo FROM seguimientos s
               JOIN procedimientos p ON p.id = s.procedimiento_id
               JOIN pacientes pa ON pa.id = p.paciente_id
               WHERE p.tipo = ? ORDER BY p.id, s.dias""", (tipo,)).fetchall()
        for f in filas:
            d = cargar_json(f["datos"])
            escritor.writerow([f["codigo"], f["procedimiento_id"], f["fecha_cirugia"], f["hito"],
                               f["fecha_prevista"], f["estado"], f["motivo_no_realizable"] or ""]
                              + [valor_legible(d.get(n)) for n in nombres])
    auditar("exportar", tipo, None, que)
    db.commit()
    # BOM UTF-8 + punto y coma: Excel en español lo abre directamente.
    return Response("﻿" + salida.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename={tipo}_{que}_{date.today()}.csv"})
