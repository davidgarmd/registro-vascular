from werkzeug.datastructures import MultiDict

from registro.formularios import (PROCEDIMIENTOS, campos, formulario_cirugia, formulario_seguimiento,
                                  procesar)

TIPOS_VALIDOS = {"texto", "area", "numero", "fecha", "select", "radio", "multi", "sino", "dispositivos", "calculado"}


def _formularios():
    for tipo in PROCEDIMIENTOS:
        yield f"{tipo}/cirugia", formulario_cirugia(tipo)
        yield f"{tipo}/reintervencion", formulario_cirugia(tipo, reintervencion=True)
        for hito in ("1m", "3m", None):
            yield f"{tipo}/seguimiento-{hito}", formulario_seguimiento(tipo, hito)


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
            for entrada in c.get("calculado", {}).get("entradas", []):
                assert entrada in vistos, f"{nombre_form}: {c['nombre']} se calcula con un campo posterior"
            for clave, texto in c.get("guia", []):
                assert clave and texto, f"{nombre_form}: guía incompleta en {c['nombre']}"
            vistos[c["nombre"]] = c


def test_incluye_todos_los_grupos_pedidos():
    assert set(PROCEDIMIENTOS) == {
        "aorta_abierta", "evar", "tevar", "bypass", "endo_periferico", "acceso_vascular",
        "viscerales", "carotida", "congestion_pelvica", "varices", "sindrome_postrombotico",
        "isquemia_aguda", "trauma",
        "amputacion", "miscelanea",
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


def test_glass_calculado():
    from registro import escalas as E
    secciones = formulario_cirugia("endo_periferico")
    base = {"edad": "75", "caracter": "Programada", "indicacion": "Isquemia crónica: lesión trófica"}
    casos = [(0, 0, E.GLASS_NA), (1, 1, "Estadio I (baja complejidad)"), (2, 1, "Estadio II (complejidad intermedia)"),
             (1, 3, "Estadio II (complejidad intermedia)"), (3, 2, "Estadio III (alta complejidad)"),
             (0, 4, "Estadio III (alta complejidad)"), (4, 0, "Estadio III (alta complejidad)")]
    for fp, ip, esperado in casos:
        datos, _ = procesar(secciones, MultiDict({**base, "glass_fp": E.GLASS_FP[fp], "glass_ip": E.GLASS_IP[ip],
                                                  "glass": "valor enviado a mano: se ignora"}))
        assert datos["glass"] == esperado, (fp, ip)
    # Sin los dos grados no hay estadio; en claudicación GLASS no se muestra.
    datos, _ = procesar(secciones, MultiDict({**base, "glass_fp": E.GLASS_FP[2]}))
    assert "glass" not in datos
    datos, _ = procesar(secciones, MultiDict({**base, "indicacion": "Claudicación intermitente",
                                              "glass_fp": E.GLASS_FP[2], "glass_ip": E.GLASS_IP[2]}))
    assert "glass_fp" not in datos and "glass" not in datos


def test_matriz_glass_completa_y_simetrica():
    from registro.escalas import TABLA_GLASS
    assert len(TABLA_GLASS) == 25
    for fp in range(5):
        for ip in range(5):
            assert TABLA_GLASS[f"{fp}|{ip}"] == TABLA_GLASS[f"{ip}|{fp}"]


def test_reintervencion_y_exitus_durante_el_ingreso():
    secciones = formulario_cirugia("varices")
    base = {"edad": "60", "caracter": "Programada", "lado": "Derecho", "ceap_c": "C2", "ejes": "Safena mayor",
            "tecnica": "Radiofrecuencia", "anestesia": "Local", "exito_tecnico": "Sí", "complicaciones": "Ninguna"}
    _, errores = procesar(secciones, MultiDict({**base, "reintervencion_ingreso": "Sí",
                                                "destino_alta": "Exitus hospitalario"}))
    assert {"reint_ingreso_fecha", "reint_ingreso_motivo", "reint_ingreso_via",
            "fecha_exitus", "causa_exitus"} <= set(errores)
    datos, errores = procesar(secciones, MultiDict({**base, "reintervencion_ingreso": "No", "destino_alta": "Domicilio",
                                                    "fecha_exitus": "2026-01-01"}))
    assert not errores and "fecha_exitus" not in datos
