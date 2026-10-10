from werkzeug.datastructures import MultiDict

from registro.formularios import (PROCEDIMIENTOS, calcular, campos, formulario_cirugia, formulario_seguimiento,
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
            regla = c.get("calculado", {})
            for entrada in regla.get("entradas", []) + regla.get("suma", []):
                assert entrada in vistos, f"{nombre_form}: {c['nombre']} se calcula con un campo posterior"
            assert set(c.get("descripciones", {})) <= set(c.get("opciones", [])), (nombre_form, c["nombre"])
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
    datos, errores = procesar(secciones, MultiDict({"edad": "200", "ceap_c": "C9", "diametro_vena_mm": "7,5"}))
    assert "edad" in errores and errores["ceap_c"] == "Opción no válida."
    assert datos["diametro_vena_mm"] == 7.5


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


def _campo(tipo, nombre, seguimiento=False):
    secciones = formulario_seguimiento(tipo) if seguimiento else formulario_cirugia(tipo)
    return next(c for c in campos(secciones) if c["nombre"] == nombre)


def test_escalas_con_descripcion_en_cada_opcion():
    asa = _campo("bypass", "asa")
    assert asa["opciones"] == ["I", "II", "III", "IV", "V"]
    assert asa["descripciones"]["III"].startswith("Enfermedad sistémica grave")
    assert "IIIb" in _campo("bypass", "clavien_dindo")["descripciones"]
    assert _campo("tevar", "zona_proximal")["descripciones"]["2"].startswith("Entre carótida")
    assert set(_campo("trauma", "grado_esvs")["opciones"]) == {"1", "2", "3", "X"}
    assert "4a" in _campo("sindrome_postrombotico", "jalaie")["opciones"]


def test_wifi_se_calcula():
    wifi = _campo("bypass", "wifi")
    assert calcular(wifi, {"wifi_w": "0", "wifi_i": "0", "wifi_fi": "0"}).startswith("Estadio 1")
    assert calcular(wifi, {"wifi_w": "1", "wifi_i": "1", "wifi_fi": "0"}).startswith("Estadio 2")
    assert calcular(wifi, {"wifi_w": "2", "wifi_i": "1", "wifi_fi": "0"}).startswith("Estadio 3")
    assert calcular(wifi, {"wifi_w": "3", "wifi_i": "1", "wifi_fi": "0"}).startswith("Estadio 4")
    assert calcular(wifi, {"wifi_w": "3", "wifi_i": "1"}) is None


def test_villalta_y_vcss_se_calculan():
    secciones = formulario_cirugia("sindrome_postrombotico")
    form = {"lado": "Izquierdo", "ceap_c": "C3", "segmentos": "Ilíaca común", "acceso": "Femoral",
            "tecnicas": "Stent venoso dedicado"}
    nombres = [c["nombre"] for c in campos(secciones)]
    for n in nombres:
        if n.startswith("villalta_") and n not in ("villalta_ulcera", "villalta_grado"):
            form[n] = "1"                                   # 11 elementos × 1 = 11 → moderado
        if n.startswith("vcss_"):
            form[n] = "2"                                   # 10 × 2 = 20
    form["villalta_ulcera"] = "No"
    datos, _ = procesar(secciones, MultiDict(form))      # faltan campos comunes: da igual aquí
    assert datos["villalta"] == 11 and datos["villalta_grado"] == "Moderado"
    assert datos["vcss"] == 20
    form["villalta_ulcera"] = "Sí"
    datos, _ = procesar(secciones, MultiDict(form))
    assert datos["villalta_grado"] == "Grave (úlcera venosa)"
    del form["vcss_dolor"]                                  # incompleto: no se calcula
    datos, _ = procesar(secciones, MultiDict(form))
    assert "vcss" not in datos


def test_codigo_svp():
    secciones = formulario_cirugia("congestion_pelvica")
    form = MultiDict([("diagnostico", "Compresión ilíaca (May-Thurner)"), ("venas_tratadas", "Ilíaca común izquierda"),
                      ("tecnica", "Stent venoso"), ("svp_s", "S2"), ("svp_s", "S3c"), ("svp_v", "V2"),
                      ("svp_anatomia", "LCIV"), ("svp_anatomia", "LIIV"), ("svp_h_LCIV", "O"),
                      ("svp_h_LIIV", "R"), ("svp_etiologia", "NT"), ("svp_h_RGV", "R")])
    datos, _ = procesar(secciones, form)
    assert datos["svp"] == "S2,3c V2 P LCIV,O,NT; LIIV,R,NT"
    assert "svp_h_RGV" not in datos                         # segmento no marcado: se descarta
