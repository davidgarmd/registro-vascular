import sqlite3
from datetime import date, timedelta
from pathlib import Path

from werkzeug.datastructures import MultiDict

from registro import modelos
from registro.cli import datos_aleatorios
from registro.formularios import PROCEDIMIENTOS, formulario_cirugia
from registro.recordatorios import enviar_recordatorios


def _procedimiento(app, dias_atras, cirujano_id=1, nhc="123456"):
    with app.app_context():
        pac = modelos.buscar_paciente_por_nhc(nhc)
        pid = pac["id"] if pac else modelos.crear_paciente(nhc, "Mujer", 1)
        fecha = (date.today() - timedelta(days=dias_atras)).isoformat()
        return modelos.crear_procedimiento(pid, "evar", fecha, cirujano_id, {"edad": 80}, 1)


def test_login_obligatorio(client):
    assert client.get("/").status_code == 302


def test_post_sin_csrf_rechazado(client):
    r = client.post("/login", data={"email": "admin@test.es", "password": "contraseña-admin"})
    assert r.status_code == 400


def test_nhc_cifrado_y_sin_duplicados(app, client, login):
    t = login()
    r = client.post("/pacientes/nuevo", data={"nhc": "00 12345", "nhc2": "00 12345", "sexo": "Hombre", "csrf_token": t})
    assert r.status_code == 302
    r = client.post("/pacientes/nuevo", data={"nhc": "0012345", "nhc2": "0012345", "sexo": "Hombre", "csrf_token": t},
                    follow_redirects=True)
    assert "ya estaba registrado como RV-00001" in r.get_data(as_text=True)
    contenido = Path(app.config["DATABASE"]).read_bytes()
    assert b"0012345" not in contenido
    assert "NHC 0012345" in client.get("/pacientes/1").get_data(as_text=True)
    assert client.get("/buscar?q=0012345").headers["Location"].endswith("/pacientes/1")


def test_flujo_completo_de_procedimiento(app, client, login):
    t = login()
    client.post("/pacientes/nuevo", data={"nhc": "999", "nhc2": "999", "sexo": "Mujer", "csrf_token": t})
    for tipo in PROCEDIMIENTOS:
        assert client.get(f"/pacientes/1/procedimientos/nuevo?tipo={tipo}").status_code == 200
    form = MultiDict({
        "csrf_token": t, "fecha_cirugia": "2026-01-15", "cirujano_id": "2",
        "edad": "78", "caracter": "Programada", "indicacion": "Aneurisma de aorta abdominal",
        "presentacion": "Asintomático", "variante": "FEVAR (fenestrada)", "acceso": "Percutáneo bilateral (PEVAR)",
        "anestesia": "General", "exito_tecnico": "Sí", "complicaciones": "Ninguna", "endofuga_final": "Ninguna",
    })
    form.setlist("vasos_diana", ["AMS", "Renal derecha", "Renal izquierda"])
    r = client.post("/pacientes/1/procedimientos/nuevo?tipo=evar", data=form)
    assert r.status_code == 302, r.get_data(as_text=True)
    with app.app_context():
        proc = modelos.obtener_procedimiento(1)
        assert proc["cirujano_id"] == 2
        segs = modelos.seguimientos_de_procedimiento(1)
        assert [s["fecha_prevista"] for s in segs] == ["2026-02-14", "2026-04-15", "2026-07-14", "2027-01-15"]
    html = client.get("/procedimientos/1").get_data(as_text=True)
    assert "FEVAR (fenestrada)" in html and "Renal izquierda" in html

    r = client.post("/seguimientos/1", data={
        "csrf_token": t, "accion": "guardar", "fecha_revision": "2026-02-20", "tipo_revision": "Presencial",
        "estado_vital": "Vivo", "reintervencion": "No", "endofuga": "Ninguna", "reingreso_30d": "No",
    })
    assert r.status_code == 302
    with app.app_context():
        assert modelos.obtener_seguimiento(1)["estado"] == "completado"

    # Cambiar la fecha de cirugía recalcula solo los pendientes.
    form["fecha_cirugia"] = "2026-01-20"
    client.post("/procedimientos/1/editar", data=form)
    with app.app_context():
        segs = modelos.seguimientos_de_procedimiento(1)
        assert segs[0]["fecha_prevista"] == "2026-02-14" and segs[1]["fecha_prevista"] == "2026-04-20"


def test_recordatorios(app):
    _procedimiento(app, dias_atras=100, cirujano_id=2)          # 1 m y 3 m vencidos
    _procedimiento(app, dias_atras=1, cirujano_id=2, nhc="2")   # nada vencido
    outbox = Path(app.config["OUTBOX"])
    hoy = date.today()
    with app.app_context():
        assert enviar_recordatorios(hoy) == {"uno@test.es": 2}
        correo = next(outbox.glob("*.eml")).read_text(encoding="utf-8")
        assert "RV-00001" in correo and "https://registro.test/seguimientos/" in correo
        assert "123456" not in correo  # el NHC nunca sale en el correo

        assert enviar_recordatorios(hoy) == {}                          # no repite el mismo día
        assert enviar_recordatorios(hoy + timedelta(days=6)) == {}      # ni antes de 7 días
        assert enviar_recordatorios(hoy + timedelta(days=7)) == {"uno@test.es": 2}

        modelos.marcar_no_realizable(1, "Trasladado a otro centro", 1)
        assert enviar_recordatorios(hoy + timedelta(days=14)) == {"uno@test.es": 1}
        assert enviar_recordatorios(hoy + timedelta(days=21)) == {"uno@test.es": 1}
        # Máximo 4 avisos por seguimiento.
        assert enviar_recordatorios(hoy + timedelta(days=28)) == {}


def test_exportacion_sin_nhc(app, client, login):
    _procedimiento(app, dias_atras=40)
    t = login()
    r = client.get("/exportar/evar/procedimientos.csv")
    texto = r.get_data(as_text=True)
    assert r.status_code == 200 and "RV-00001" in texto and "123456" not in texto
    assert client.get("/exportar/evar/seguimientos.csv").status_code == 200


def test_cirujano_no_admin_no_exporta(client, login):
    login("uno@test.es", "contraseña-uno")
    assert client.get("/exportar").status_code == 403
    assert client.get("/usuarios").status_code == 403


def test_demo_rellena_formularios_validos(app):
    import random
    rng = random.Random(1)
    for tipo in PROCEDIMIENTOS:
        for _ in range(20):
            datos = datos_aleatorios(formulario_cirugia(tipo), rng)
            assert datos["edad"] >= 14


def test_todas_las_paginas_cargan(app, client, login):
    t = login()
    runner = app.test_cli_runner()
    assert "Demo cargada" in runner.invoke(args=["demo", "--pacientes", "22"]).output
    for url in ["/", "/pacientes", "/seguimientos", "/seguimientos?mios=1&vencidos=0", "/usuarios",
                "/exportar", "/perfil", "/pacientes/5", "/procedimientos/5", "/procedimientos/5/editar",
                "/seguimientos/3", "/pacientes/1/procedimientos/nuevo"]:
        assert client.get(url).status_code == 200, url
    r = client.post("/admin/recordatorios", data={"csrf_token": t}, follow_redirects=True)
    assert r.status_code == 200


def test_programador_envia_una_vez_al_dia(app):
    from datetime import datetime
    from registro.programador import comprobar
    _procedimiento(app, dias_atras=40, cirujano_id=2)
    hoy = date.today()
    temprano = datetime(hoy.year, hoy.month, hoy.day, 7, 0)
    assert comprobar(app, temprano) is None                     # antes de la hora
    assert comprobar(app, temprano.replace(hour=11)) == {"uno@test.es": 1}
    assert comprobar(app, temprano.replace(hour=15)) is None    # ya enviado hoy


def test_bloqueo_tras_intentos_fallidos(client):
    from tests.conftest import token
    for _ in range(5):
        r = client.post("/login", data={"email": "uno@test.es", "password": "mala", "csrf_token": token(client)})
        assert r.status_code == 200
    # Ni siquiera la contraseña correcta entra durante el bloqueo.
    r = client.post("/login", data={"email": "uno@test.es", "password": "contraseña-uno", "csrf_token": token(client)})
    assert r.status_code == 429
    # Otra cuenta sigue pudiendo entrar.
    r = client.post("/login", data={"email": "admin@test.es", "password": "contraseña-admin", "csrf_token": token(client)})
    assert r.status_code == 302


def _paciente_y_bypass(app, client, t):
    client.post("/pacientes/nuevo", data={"nhc": "777", "nhc2": "777", "sexo": "Hombre", "csrf_token": t})
    form = MultiDict({
        "csrf_token": t, "fecha_cirugia": "2026-03-01", "cirujano_id": "1", "edad": "70",
        "caracter": "Programada", "indicacion": "Claudicación intermitente", "lado": "Derecho",
        "tipo_bypass": "Fémoro-poplíteo supragenicular", "conducto": "PTFE", "profundoplastia": "Sí",
        "hibrido": "Sí", "sector_hibrido": "Aortoilíaco (entrada)", "tecnicas_hibrido": "Angioplastia simple",
        "anestesia": "General", "exito_tecnico": "Sí", "complicaciones": "Ninguna",
    })
    # Dos dispositivos con medidas; la fila vacía del final se ignora.
    form.setlist("dispositivos__tipo", ["Stent cubierto autoexpandible", "Balón", ""])
    form.setlist("dispositivos__vaso", ["Ilíaca externa", "", ""])
    form.setlist("dispositivos__modelo", ["Viabahn", "", ""])
    form.setlist("dispositivos__diametro", ["8", "7", ""])
    form.setlist("dispositivos__longitud", ["50", "40", ""])
    r = client.post("/pacientes/1/procedimientos/nuevo?tipo=bypass", data=form)
    assert r.status_code == 302, r.get_data(as_text=True)
    return form


def test_bypass_hibrido_con_dispositivos(app, client, login):
    t = login()
    _paciente_y_bypass(app, client, t)
    with app.app_context():
        import json
        datos = json.loads(modelos.obtener_procedimiento(1)["datos"])
    assert datos["profundoplastia"] == "Sí"
    assert datos["dispositivos"] == [
        {"tipo": "Stent cubierto autoexpandible", "vaso": "Ilíaca externa", "modelo": "Viabahn",
         "diametro": 8, "longitud": 50},
        {"tipo": "Balón", "diametro": 7, "longitud": 40},
    ]
    html = client.get("/procedimientos/1").get_data(as_text=True)
    assert "Stent cubierto autoexpandible 8×50 mm (Viabahn) en Ilíaca externa" in html
    texto = client.get("/exportar/bypass/procedimientos.csv").get_data(as_text=True)
    assert "Balón 7×40 mm" in texto


def test_dispositivo_sin_tipo_da_error(app, client, login):
    from registro.formularios import procesar, formulario_cirugia
    form = MultiDict({"edad": "70", "caracter": "Programada"})
    form.setlist("dispositivos__tipo", [""])
    form.setlist("dispositivos__diametro", ["6"])
    _, errores = procesar(formulario_cirugia("endo_periferico"), form)
    assert "tipo de dispositivo" in errores["dispositivos"]


def test_reintervencion_enlazada(app, client, login):
    t = login()
    _paciente_y_bypass(app, client, t)
    # La pantalla de elección ofrece enlazar con la intervención previa.
    assert "Reintervención de: Bypass periférico" in client.get("/pacientes/1/procedimientos/nuevo").get_data(as_text=True)
    form = {
        "csrf_token": t, "fecha_cirugia": "2026-06-01", "cirujano_id": "1", "edad": "70",
        "caracter": "Urgente (< 72 h)", "reint_motivo": "Trombosis/oclusión",
        "reint_relacion": "Sobre el mismo procedimiento/lesión diana", "extremidad": "Miembro inferior derecho",
        "etiologia": "Trombosis de bypass", "rutherford_agudo": "IIa - Amenaza marginal", "abordaje": "Femoral",
        "embolectomia": "Sí", "direccion_embolectomia": "Distal", "territorios": "Poplítea",
        "tromboaspiracion": "Sí", "anestesia": "General", "exito_tecnico": "Sí", "complicaciones": "Ninguna",
    }
    # Sin «con_seguimiento»: no programa seguimientos propios.
    r = client.post("/pacientes/1/procedimientos/nuevo?tipo=isquemia_aguda&origen=1", data=form)
    assert r.status_code == 302, r.get_data(as_text=True)
    with app.app_context():
        reint = modelos.obtener_procedimiento(2)
        assert reint["procedimiento_origen_id"] == 1 and reint["con_seguimiento"] == 0
        assert modelos.seguimientos_de_procedimiento(2) == []
        assert len(modelos.seguimientos_de_procedimiento(1)) == 4     # el original sigue igual
        assert [(p["id"], n) for p, n in modelos.arbol_de_paciente(1)] == [(1, 0), (2, 1)]
    html = client.get("/procedimientos/1").get_data(as_text=True)
    assert "Reintervenciones sobre esta intervención" in html
    assert "Reintervención de:" in client.get("/procedimientos/2").get_data(as_text=True)
    # Con seguimiento propio.
    r = client.post("/pacientes/1/procedimientos/nuevo?tipo=isquemia_aguda&origen=2",
                    data={**form, "con_seguimiento": "1"})
    with app.app_context():
        assert len(modelos.seguimientos_de_procedimiento(3)) == 4
        assert [n for _, n in modelos.arbol_de_paciente(1)] == [0, 1, 2]
    # No se puede enlazar con una intervención de otro paciente.
    client.post("/pacientes/nuevo", data={"nhc": "888", "nhc2": "888", "sexo": "Mujer", "csrf_token": t})
    assert client.get("/pacientes/2/procedimientos/nuevo?tipo=bypass&origen=1").status_code == 400
    csv = client.get("/exportar/isquemia_aguda/procedimientos.csv").get_data(as_text=True)
    assert "Trombosis/oclusión" in csv


def test_seguimiento_30_dias_solo_al_mes_y_mortalidad(app, client, login):
    t = login()
    _procedimiento(app, dias_atras=100)
    assert "Reingreso hospitalario" in client.get("/seguimientos/1").get_data(as_text=True)
    assert "Reingreso hospitalario" not in client.get("/seguimientos/2").get_data(as_text=True)
    with app.app_context():
        fecha = modelos.obtener_procedimiento(1)["fecha_cirugia"]
    muerte = (date.fromisoformat(fecha) + timedelta(days=20)).isoformat()
    r = client.post("/seguimientos/1", data={
        "csrf_token": t, "accion": "guardar", "fecha_revision": muerte, "tipo_revision": "Revisión de historia clínica",
        "estado_vital": "Fallecido", "fecha_fallecimiento": muerte, "causa_muerte": "Cardiovascular",
        "reintervencion": "No", "reingreso_30d": "Sí", "reingreso_motivo": "Causa cardiaca",
    })
    assert r.status_code == 302
    texto = client.get("/exportar/evar/seguimientos.csv").get_data(as_text=True)
    fila_1m = next(l for l in texto.splitlines() if ";1m;" in l)
    assert ";Sí;" in fila_1m and "Causa cardiaca" in fila_1m


def test_migracion_de_base_antigua(tmp_path):
    import sqlite3
    from cryptography.fernet import Fernet
    from registro import create_app
    from registro.db import init_db
    ruta = tmp_path / "antigua.sqlite3"
    con = sqlite3.connect(ruta)
    con.executescript("""CREATE TABLE procedimientos (id INTEGER PRIMARY KEY, paciente_id INTEGER, cirujano_id INTEGER,
        tipo TEXT, fecha_cirugia TEXT, datos TEXT, creado TEXT, creado_por INTEGER, modificado TEXT, modificado_por INTEGER);
        INSERT INTO procedimientos (id, tipo) VALUES (1, 'evar');""")
    con.commit(); con.close()
    app = create_app({"TESTING": True, "SECRET_KEY": "x", "NHC_KEY": Fernet.generate_key().decode(),
                      "HMAC_KEY": "k", "DATABASE": str(ruta)})
    with app.app_context():
        init_db()
        init_db()  # idempotente
    fila = sqlite3.connect(ruta).execute("SELECT procedimiento_origen_id, con_seguimiento FROM procedimientos").fetchone()
    assert fila == (None, 1)
