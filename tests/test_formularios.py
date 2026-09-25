from werkzeug.datastructures import MultiDict

from registro.formularios import (PROCEDIMIENTOS, campos, formulario_cirugia, formulario_seguimiento,
                                  procesar)

TIPOS_VALIDOS = {"texto", "area", "numero", "fecha", "select", "radio", "multi", "sino"}


def _formularios():
    for tipo in PROCEDIMIENTOS:
        yield f"{tipo}/cirugia", formulario_cirugia(tipo)
        yield f"{tipo}/seguimiento", formulario_seguimiento(tipo)


def test_esquemas_coherentes():
    for nombre_form, secciones in _formularios():
        vistos = {}
        for c in campos(secciones):
            assert c["tipo"] in TIPOS_VALIDOS, (nombre_form, c["nombre"])
            assert c["nombre"] not in vistos, f"{nombre_form}: campo duplicado {c['nombre']}"
            if c["tipo"] in ("select", "radio", "multi", "sino"):
                assert c["opciones"] and len(set(c["opciones"])) == len(c["opciones"]), (nombre_form, c["nombre"])
            conds = c.get("si") or []
            for cond in [conds] if isinstance(conds, dict) else conds:
                padre = vistos.get(cond["campo"])
                assert padre is not None, f"{nombre_form}: {c['nombre']} depende de un campo posterior o inexistente"
                referidos = cond.get("valores", []) + cond.get("excepto", [])
                assert set(referidos) <= set(padre["opciones"]), f"{nombre_form}: {c['nombre']} usa valores inexistentes"
            vistos[c["nombre"]] = c


def test_incluye_todos_los_grupos_pedidos():
    assert set(PROCEDIMIENTOS) == {
        "aorta_abierta", "evar", "tevar", "bypass", "endo_periferico", "acceso_vascular",
        "viscerales", "carotida", "congestion_pelvica", "varices", "miscelanea",
    }


def test_campos_ocultos_se_descartan_y_obligatorios_visibles_se_exigen():
    secciones = formulario_cirugia("carotida")
    form = MultiDict({
        "edad": "71", "caracter": "Programada", "sintomatologia": "Asintomática", "lado": "Derecho",
        "estenosis": "70-99 %", "abordaje": "Abierto",
        "tecnica_endo": "CAS transfemoral",       # oculto (abordaje abierto): debe descartarse
        "dias_desde_sintoma": "5",                 # oculto (asintomática)
        "anestesia": "General", "exito_tecnico": "Sí", "complicaciones": "Ninguna",
    })
    datos, errores = procesar(secciones, form)
    assert "tecnica_endo" not in datos and "dias_desde_sintoma" not in datos
    assert errores == {"tecnica_abierta": "Campo obligatorio."}


def test_numeros_fuera_de_rango_y_opciones_invalidas():
    secciones = formulario_cirugia("varices")
    datos, errores = procesar(secciones, MultiDict({"edad": "200", "ceap_c": "C9", "vcss": "3,0"}))
    assert "edad" in errores and errores["ceap_c"] == "Opción no válida."
    assert datos["vcss"] == 3


def test_excepto():
    secciones = formulario_cirugia("bypass")
    base = {"edad": "70", "caracter": "Programada", "lado": "Derecho"}
    datos, _ = procesar(secciones, MultiDict({**base, "indicacion": "Isquemia aguda", "rutherford": "4 - Dolor en reposo"}))
    assert "rutherford" not in datos
    datos, _ = procesar(secciones, MultiDict({**base, "indicacion": "Claudicación intermitente", "rutherford": "3 - Claudicación grave"}))
    assert datos["rutherford"] == "3 - Claudicación grave"
