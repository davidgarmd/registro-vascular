"""Definición de los formularios dinámicos del registro.

Cada formulario es una lista de secciones; cada sección tiene un título y una
lista de campos. Un campo es un diccionario con:

    nombre     identificador interno (único dentro del formulario)
    etiqueta   texto que ve el usuario
    tipo       texto | area | numero | fecha | select | radio | multi | sino
    opciones   lista de valores (select, radio, multi)
    req        obligatorio cuando el campo está visible
    si         condición de visibilidad: {"campo": x, "valores": [...]}
               o {"campo": x, "excepto": [...]}; admite una lista (todas deben cumplirse).
               Solo puede referirse a campos anteriores del mismo formulario.
    min, max   límites para campos numéricos
    unidad     texto que se muestra tras un campo numérico
    ayuda      aclaración breve

Para añadir o cambiar variables basta con editar este fichero: los datos se
guardan como JSON, así que no hace falta tocar la base de datos.
"""

SINO = ["Sí", "No"]
LADO = ["Derecho", "Izquierdo", "Bilateral"]


def C(nombre, etiqueta, tipo="texto", opciones=None, req=False, si=None, **extra):
    campo = {"nombre": nombre, "etiqueta": etiqueta, "tipo": tipo, "req": req}
    if tipo == "sino":
        opciones = SINO
    if opciones is not None:
        campo["opciones"] = list(opciones)
    if si is not None:
        campo["si"] = si
    campo.update(extra)
    return campo


def S(titulo, *campos):
    return {"titulo": titulo, "campos": list(campos)}


def si(campo, *valores):
    return {"campo": campo, "valores": list(valores)}


def excepto(campo, *valores):
    return {"campo": campo, "excepto": list(valores)}


# ---------------------------------------------------------------------------
# Secciones comunes a todos los procedimientos
# ---------------------------------------------------------------------------

ANTITROMBOTICOS = [
    "Ninguno", "AAS", "Clopidogrel", "Otro antiagregante", "Anticoagulante oral",
    "Rivaroxabán 2,5 mg/12 h (dosis vascular)", "HBPM",
]

COMUN_PREOPERATORIO = [
    S(
        "Datos basales",
        C("edad", "Edad en la cirugía", "numero", req=True, min=14, max=110, unidad="años"),
        C("imc", "IMC", "numero", min=10, max=70, unidad="kg/m²"),
        C("factores_riesgo", "Factores de riesgo y comorbilidad", "multi", [
            "HTA", "Diabetes mellitus", "Dislipemia", "Cardiopatía isquémica",
            "Insuficiencia cardiaca", "Fibrilación auricular", "EPOC",
            "Enfermedad renal crónica (FG < 60)", "Diálisis", "Ictus/AIT previo",
            "Neoplasia activa", "Ninguno",
        ]),
        C("tabaquismo", "Tabaquismo", "radio", ["Nunca", "Exfumador (> 1 año)", "Fumador activo"]),
        C("asa", "ASA", "select", ["I", "II", "III", "IV", "V"]),
        C("antitromboticos_preop", "Tratamiento antitrombótico previo", "multi", ANTITROMBOTICOS),
        C("caracter", "Carácter de la intervención", "radio",
          ["Programada", "Urgente (< 72 h)", "Emergente"], req=True),
    ),
]

COMUN_INTRAOPERATORIO = S(
    "Datos generales de la intervención",
    C("anestesia", "Anestesia", "select", [
        "General", "Raquídea/epidural", "Bloqueo locorregional", "Local",
        "Local + sedación", "Tumescente",
    ], req=True),
    C("duracion_min", "Duración", "numero", min=0, max=1440, unidad="min"),
    C("transfusion_ch", "Concentrados de hematíes transfundidos", "numero", min=0, max=100),
    C("exito_tecnico", "Éxito técnico", "sino", req=True),
)

COMUN_POSTOPERATORIO = [
    S(
        "Postoperatorio (hasta el alta)",
        C("complicaciones", "Complicaciones", "multi", [
            "Ninguna", "IAM/SCA", "Arritmia", "Insuficiencia cardiaca", "Ictus/AIT",
            "Insuficiencia respiratoria/neumonía", "Insuficiencia renal aguda",
            "Necesidad de diálisis", "Isquemia intestinal",
            "Isquemia medular (paraplejía/paraparesia)", "Hemorragia/hematoma",
            "Complicación del acceso", "Infección de herida", "Linfocele/linforrea",
            "Trombosis/fallo precoz", "Lesión nerviosa", "Delirium", "Otra",
        ], req=True),
        C("complicaciones_otra", "Otra complicación (especificar)", si=si("complicaciones", "Otra")),
        C("reintervencion_ingreso", "Reintervención durante el ingreso", "sino"),
        C("clavien_dindo", "Clavien-Dindo (peor complicación)", "select",
          ["0 (sin complicaciones)", "I", "II", "IIIa", "IIIb", "IVa", "IVb", "V"]),
        C("estancia_uci_dias", "Estancia en UCI/REA", "numero", min=0, max=365, unidad="días"),
        C("estancia_dias", "Estancia hospitalaria total", "numero", min=0, max=365, unidad="días"),
        C("destino_alta", "Destino al alta", "select", [
            "Domicilio", "Centro sociosanitario", "Traslado a otro hospital",
            "Exitus hospitalario",
        ]),
        C("comentarios_cirugia", "Comentarios", "area"),
    ),
]

COMUN_SEGUIMIENTO = [
    S(
        "Estado del paciente",
        C("fecha_revision", "Fecha de la revisión", "fecha", req=True),
        C("tipo_revision", "Tipo de revisión", "radio",
          ["Presencial", "Telefónica", "Revisión de historia clínica"], req=True),
        C("estado_vital", "Estado vital", "radio", ["Vivo", "Fallecido"], req=True),
        C("fecha_fallecimiento", "Fecha de fallecimiento", "fecha", si=si("estado_vital", "Fallecido")),
        C("causa_muerte", "Causa de la muerte", "select", [
            "Relacionada con el procedimiento", "Cardiovascular", "Otra causa", "Desconocida",
        ], si=si("estado_vital", "Fallecido")),
        C("reintervencion", "Reintervención relacionada desde la última revisión", "sino", req=True),
        C("reintervencion_fecha", "Fecha de la reintervención", "fecha", si=si("reintervencion", "Sí")),
        C("reintervencion_via", "Vía", "radio", ["Abierta", "Endovascular", "Híbrida"],
          si=si("reintervencion", "Sí")),
        C("reintervencion_motivo", "Motivo", "area", si=si("reintervencion", "Sí")),
        C("eventos", "Eventos desde la última revisión", "multi", [
            "Ninguno", "IAM/SCA", "Ictus/AIT", "Ingreso por insuficiencia cardiaca",
            "Inicio de diálisis", "Amputación mayor", "Infección de herida/injerto", "Otro",
        ]),
        C("antitromboticos", "Tratamiento antitrombótico actual", "multi", ANTITROMBOTICOS,
          si=si("estado_vital", "Vivo")),
        C("estatina", "Toma estatina", "sino", si=si("estado_vital", "Vivo")),
        C("imagen", "Prueba de imagen realizada", "multi",
          ["Ninguna", "Eco-doppler", "AngioTC", "AngioRM", "Arteriografía/flebografía"]),
    ),
]

# ---------------------------------------------------------------------------
# Bloques reutilizables
# ---------------------------------------------------------------------------

ENDOFUGAS = ["Ninguna", "Tipo Ia", "Tipo Ib", "Tipo II", "Tipo III", "Tipo IV"]
RUTHERFORD = [
    "0 - Asintomático", "1 - Claudicación leve", "2 - Claudicación moderada",
    "3 - Claudicación grave", "4 - Dolor en reposo", "5 - Pérdida tisular menor",
    "6 - Pérdida tisular mayor",
]
INDICACION_PERIFERICA = [
    "Claudicación intermitente", "Isquemia crónica: dolor en reposo",
    "Isquemia crónica: lesión trófica", "Isquemia aguda", "Aneurisma poplíteo",
    "Traumatismo", "Rescate de bypass/stent previo", "Otra",
]
WIFI = [
    C("wifi_w", "WIfI - Herida (W)", "select", ["0", "1", "2", "3"],
      si=si("indicacion", "Isquemia crónica: lesión trófica")),
    C("wifi_i", "WIfI - Isquemia (I)", "select", ["0", "1", "2", "3"],
      si=si("indicacion", "Isquemia crónica: lesión trófica")),
    C("wifi_fi", "WIfI - Infección del pie (fI)", "select", ["0", "1", "2", "3"],
      si=si("indicacion", "Isquemia crónica: lesión trófica")),
]
SEGUIMIENTO_EXTREMIDAD = [
    C("rutherford_actual", "Rutherford actual", "select", RUTHERFORD),
    C("itb", "Índice tobillo-brazo", "numero", min=0, max=3, ayuda="Usa punto decimal: 0.85"),
    C("amputacion_mayor", "Amputación mayor", "radio", ["No", "Infracondílea", "Supracondílea"]),
    C("amputacion_menor", "Amputación menor (dedos/transmetatarsiana)", "sino"),
    C("cicatrizacion", "Lesión trófica", "select",
      ["No aplica", "Cicatrizada", "En proceso de cicatrización", "Sin cambios", "Empeora"]),
]
SEGUIMIENTO_AORTA_ENDO = [
    C("diametro_saco_mm", "Diámetro máximo del saco", "numero", min=0, max=150, unidad="mm"),
    C("evolucion_saco", "Evolución del saco", "radio",
      ["Regresión ≥ 5 mm", "Estable", "Crecimiento ≥ 5 mm", "No valorable"]),
    C("endofuga", "Endofuga", "multi", ENDOFUGAS + ["Endotensión (tipo V)", "No valorable"]),
    C("migracion", "Migración (> 10 mm)", "sino"),
    C("vasos_diana_ocluidos", "Oclusión/estenosis de vasos diana o ramas", "multi", [
        "No aplica", "Ninguna", "Tronco celíaco", "AMS", "Renal derecha", "Renal izquierda",
        "Subclavia izquierda", "Rama ilíaca/hipogástrica",
    ]),
    C("trombosis_rama_iliaca", "Trombosis de rama ilíaca", "sino"),
    C("creatinina", "Creatinina", "numero", min=0, max=20, unidad="mg/dl"),
]

# ---------------------------------------------------------------------------
# Procedimientos
# ---------------------------------------------------------------------------

PROCEDIMIENTOS = {}


def procedimiento(clave, nombre, descripcion, secciones, seguimiento):
    PROCEDIMIENTOS[clave] = {
        "clave": clave, "nombre": nombre, "descripcion": descripcion,
        "secciones": secciones, "seguimiento": seguimiento,
    }


# Aorta abierta --------------------------------------------------------------
_aneurismas = ["Aneurisma de aorta abdominal", "Aneurisma ilíaco aislado",
               "Aneurisma toracoabdominal", "Conversión tardía tras EVAR"]
_clampaje_alto = ["Entre arterias renales", "Suprarrenal", "Supracelíaco", "Aorta torácica"]
procedimiento(
    "aorta_abierta", "Aorta abierta",
    "Reparación abierta de aneurisma, enfermedad oclusiva aortoilíaca o infección aórtica.",
    [
        S(
            "Indicación y anatomía",
            C("indicacion", "Indicación", "select", _aneurismas + [
                "Enfermedad oclusiva aortoilíaca", "Infección de prótesis/aortitis",
                "Fístula aortoentérica", "Otra",
            ], req=True),
            C("presentacion", "Presentación", "radio", ["Asintomático", "Sintomático no roto", "Roto"],
              si=si("indicacion", *_aneurismas)),
            C("diametro_max_mm", "Diámetro máximo", "numero", min=0, max=150, unidad="mm",
              si=si("indicacion", *_aneurismas)),
            C("extension", "Extensión", "select", [
                "Infrarrenal", "Yuxtarrenal", "Pararrenal", "Suprarrenal", "Toracoabdominal",
            ], si=si("indicacion", *_aneurismas)),
            C("crawford", "Clasificación de Crawford", "select", ["I", "II", "III", "IV", "V"],
              si=si("extension", "Toracoabdominal")),
            C("tasc_aortoiliaco", "TASC II aortoilíaco", "select", ["A", "B", "C", "D"],
              si=si("indicacion", "Enfermedad oclusiva aortoilíaca")),
            C("rutherford", "Rutherford", "select", RUTHERFORD,
              si=si("indicacion", "Enfermedad oclusiva aortoilíaca")),
        ),
        S(
            "Técnica",
            C("abordaje", "Abordaje", "radio",
              ["Laparotomía transperitoneal", "Retroperitoneal", "Toracofrenolaparotomía"], req=True),
            C("clampaje", "Nivel de clampaje proximal", "select", ["Infrarrenal"] + _clampaje_alto, req=True),
            C("isquemia_renal_min", "Tiempo de isquemia renal", "numero", min=0, max=300, unidad="min",
              si=si("clampaje", *_clampaje_alto)),
            C("proteccion_renal", "Protección renal", "multi",
              ["Ninguna", "Suero frío", "Custodiol", "Perfusión con sangre"],
              si=si("clampaje", *_clampaje_alto)),
            C("reconstruccion", "Reconstrucción", "select", [
                "Tubo recto", "Aorto-biilíaco", "Aorto-bifemoral", "Aorto-unifemoral/uniilíaco",
                "Explante + reconstrucción in situ", "Explante + bypass extraanatómico", "Otra",
            ], req=True),
            C("injerto", "Material del injerto", "select", [
                "Dacron", "Dacron impregnado en plata/antibiótico", "PTFE",
                "Aloinjerto criopreservado", "Vena femoral (NAIS)", "Pericardio bovino",
            ]),
            C("procedimientos_asociados", "Procedimientos asociados", "multi", [
                "Ninguno", "Reimplante de AMI", "Revascularización renal",
                "Revascularización visceral", "Revascularización hipogástrica",
            ]),
            C("recuperador_celular", "Recuperador celular", "sino"),
            C("drenaje_lcr", "Drenaje de LCR", "sino", si=si("extension", "Toracoabdominal")),
        ),
    ],
    [S("Seguimiento específico",
       C("complicacion_injerto", "Complicación del injerto", "multi", [
           "Ninguna", "Pseudoaneurisma anastomótico", "Infección protésica",
           "Trombosis de rama", "Fístula aortoentérica",
       ]),
       C("eventracion", "Eventración/hernia incisional", "sino"),
       C("disfuncion_sexual", "Disfunción sexual nueva", "sino"),
       C("creatinina", "Creatinina", "numero", min=0, max=20, unidad="mg/dl"),
       )],
)

# EVAR / FEVAR / BEVAR -------------------------------------------------------
_complejos = ["FEVAR (fenestrada)", "BEVAR (ramificada)", "ChEVAR (chimeneas)"]
_percutaneo = ["Percutáneo bilateral (PEVAR)", "Percutáneo + abierto"]
procedimiento(
    "evar", "EVAR / FEVAR / BEVAR",
    "Reparación endovascular de aorta abdominal: estándar, fenestrada, ramificada. El acceso "
    "percutáneo (PEVAR) se registra en el campo de acceso.",
    [
        S(
            "Indicación y anatomía",
            C("indicacion", "Indicación", "select", [
                "Aneurisma de aorta abdominal", "Aneurisma aortoilíaco", "Aneurisma ilíaco aislado",
                "Aneurisma yuxta/pararrenal", "Aneurisma toracoabdominal",
                "Pseudoaneurisma anastomótico", "Reintervención sobre EVAR previo", "Otra",
            ], req=True),
            C("presentacion", "Presentación", "radio", ["Asintomático", "Sintomático", "Roto"], req=True),
            C("diametro_max_mm", "Diámetro máximo", "numero", min=0, max=150, unidad="mm"),
            C("cuello_longitud_mm", "Longitud del cuello", "numero", min=0, max=100, unidad="mm"),
            C("cuello_diametro_mm", "Diámetro del cuello", "numero", min=0, max=60, unidad="mm"),
            C("cuello_angulacion", "Angulación del cuello", "numero", min=0, max=180, unidad="grados"),
        ),
        S(
            "Técnica",
            C("variante", "Variante", "radio", ["EVAR estándar"] + _complejos + ["Otra (EVAS…)"], req=True),
            C("tipo_dispositivo", "Tipo de dispositivo", "radio",
              ["A medida (custom-made)", "Estándar (off-the-shelf)", "Modificada por el cirujano (PMEG)"],
              si=si("variante", *_complejos[:2])),
            C("vasos_diana", "Vasos diana", "multi",
              ["Tronco celíaco", "AMS", "Renal derecha", "Renal izquierda", "Renal accesoria"],
              si=si("variante", *_complejos), req=True),
            C("stents_puente", "Stents puente", "multi",
              ["Cubierto balón-expandible", "Cubierto autoexpandible", "Metálico desnudo de refuerzo"],
              si=si("variante", *_complejos)),
            C("dispositivo", "Endoprótesis (marca/modelo)"),
            C("acceso", "Acceso femoral", "radio",
              _percutaneo + ["Quirúrgico abierto", "Conducto ilíaco"], req=True),
            C("cierre_percutaneo", "Dispositivo de cierre", "select",
              ["ProGlide (preclose)", "MANTA", "Otro"], si=si("acceso", *_percutaneo)),
            C("fallo_cierre", "Fallo del cierre percutáneo (conversión a abierto)", "sino",
              si=si("acceso", *_percutaneo)),
            C("acceso_superior", "Acceso superior", "select", ["No", "Axilar", "Braquial", "Carotídeo"]),
            C("hipogastricas", "Manejo de hipogástricas", "multi", [
                "No aplica", "Rama ilíaca (IBE) derecha", "Rama ilíaca (IBE) izquierda",
                "Embolización hipogástrica derecha", "Embolización hipogástrica izquierda",
                "Cobertura sin embolizar",
            ]),
            C("drenaje_lcr", "Drenaje de LCR", "sino", si=si("variante", *_complejos)),
            C("contraste_ml", "Contraste", "numero", min=0, max=1000, unidad="ml"),
            C("fluoroscopia_min", "Tiempo de fluoroscopia", "numero", min=0, max=600, unidad="min"),
            C("dosis_radiacion", "Dosis (DAP)", "numero", min=0, unidad="Gy·cm²"),
            C("endofuga_final", "Endofuga en la angiografía final", "multi", ENDOFUGAS, req=True),
        ),
    ],
    [S("Seguimiento específico", *SEGUIMIENTO_AORTA_ENDO,
       C("claudicacion_glutea", "Claudicación glútea", "sino"),
       C("isquemia_colon", "Isquemia colónica", "sino"))],
)

# TEVAR ----------------------------------------------------------------------
_disecciones = ["Disección tipo B", "Hematoma intramural"]
_subclavia_rev = ["Rama de la endoprótesis", "Bypass carótido-subclavio",
                  "Transposición subclavio-carotídea", "Fenestración in situ/chimenea"]
procedimiento(
    "tevar", "TEVAR",
    "Reparación endovascular de aorta torácica: estándar o con rama para subclavia.",
    [
        S(
            "Indicación y anatomía",
            C("patologia", "Patología", "select", [
                "Aneurisma de aorta torácica descendente", "Disección tipo B", "Hematoma intramural",
                "Úlcera penetrante", "Traumatismo aórtico", "Pseudoaneurisma",
                "Falsa luz tras disección tipo A", "Otra",
            ], req=True),
            C("fase_diseccion", "Fase", "select", [
                "Hiperaguda (< 24 h)", "Aguda (1-14 días)", "Subaguda (15-90 días)", "Crónica (> 90 días)",
            ], si=si("patologia", *_disecciones)),
            C("complicada", "Situación clínica", "radio",
              ["No complicada", "De alto riesgo", "Complicada (rotura/malperfusión)"],
              si=si("patologia", *_disecciones)),
            C("presentacion", "Presentación", "radio", ["Asintomático", "Sintomático", "Roto"]),
            C("diametro_max_mm", "Diámetro máximo", "numero", min=0, max=150, unidad="mm"),
        ),
        S(
            "Técnica",
            C("variante", "Variante", "radio", [
                "TEVAR estándar", "TEVAR con rama para subclavia izquierda",
                "TEVAR con ramas/fenestraciones para troncos supraaórticos", "TEVAR + debranching quirúrgico",
            ], req=True),
            C("zona_proximal", "Zona de anclaje proximal (Ishimaru)", "select", ["0", "1", "2", "3", "4"], req=True),
            C("subclavia", "Arteria subclavia izquierda", "select",
              ["No cubierta", "Cubierta sin revascularizar"] + _subclavia_rev, req=True),
            C("extension_distal", "Extensión distal de la cobertura", "select",
              ["Por encima de T8", "T8-T10", "Hasta tronco celíaco"]),
            C("dispositivo", "Endoprótesis (marca/modelo)"),
            C("n_modulos", "Número de módulos", "numero", min=1, max=10),
            C("drenaje_lcr", "Drenaje de LCR", "radio", ["No", "Profiláctico", "Terapéutico"]),
            C("acceso", "Acceso", "radio", ["Percutáneo", "Quirúrgico abierto", "Conducto ilíaco"], req=True),
            C("contraste_ml", "Contraste", "numero", min=0, max=1000, unidad="ml"),
            C("fluoroscopia_min", "Tiempo de fluoroscopia", "numero", min=0, max=600, unidad="min"),
            C("endofuga_final", "Endofuga en la angiografía final", "multi", ENDOFUGAS, req=True),
        ),
    ],
    [S("Seguimiento específico", *SEGUIMIENTO_AORTA_ENDO,
       C("falsa_luz", "Falsa luz torácica", "select",
         ["No aplica", "Trombosis completa", "Trombosis parcial", "Permeable"]),
       C("rtad", "Disección retrógrada tipo A", "sino"),
       C("sine", "Nueva entrada distal inducida por el stent (dSINE)", "sino"),
       C("isquemia_brazo", "Isquemia del brazo izquierdo", "sino"),
       C("paraplejia_tardia", "Isquemia medular tardía", "sino"))],
)

# Bypass ---------------------------------------------------------------------
_distales = ["Fémoro-distal", "Poplíteo-distal", "Pedio/plantar"]
procedimiento(
    "bypass", "Bypass periférico",
    "Revascularización quirúrgica de miembros inferiores y bypass extraanatómicos.",
    [
        S(
            "Indicación",
            C("indicacion", "Indicación", "select", INDICACION_PERIFERICA, req=True),
            C("lado", "Lado", "radio", LADO, req=True),
            C("rutherford", "Rutherford", "select", RUTHERFORD,
              si=excepto("indicacion", "Isquemia aguda", "Aneurisma poplíteo", "Traumatismo")),
            *WIFI,
            C("rutherford_agudo", "Clasificación de isquemia aguda", "select", ["I", "IIa", "IIb", "III"],
              si=si("indicacion", "Isquemia aguda")),
            C("glass", "GLASS", "select", ["I", "II", "III"]),
            C("redo", "Revascularización previa en esta extremidad", "sino"),
        ),
        S(
            "Técnica",
            C("tipo_bypass", "Tipo de bypass", "select", [
                "Aorto/ilio-femoral", "Fémoro-femoral cruzado", "Axilo-femoral/bifemoral",
                "Fémoro-poplíteo supragenicular", "Fémoro-poplíteo infragenicular",
            ] + _distales + ["Otro"], req=True),
            C("vaso_distal", "Vaso receptor distal", "select",
              ["Tibial anterior", "Tronco tibioperoneo", "Tibial posterior", "Peronea", "Pedia", "Plantar"],
              si=si("tipo_bypass", *_distales)),
            C("conducto", "Conducto", "select", [
                "Safena mayor invertida", "Safena mayor in situ", "Safena mayor no invertida",
                "Safena menor/venas del brazo", "Compuesto (prótesis + vena)", "PTFE",
                "PTFE heparinizado", "Dacron", "Aloinjerto criopreservado",
            ], req=True),
            C("endarterectomia_femoral", "Endarterectomía femoral asociada", "sino"),
            C("hibrido", "Procedimiento híbrido (endovascular asociado)", "sino"),
            C("amputacion_menor_asociada", "Amputación menor/desbridamiento asociado", "sino"),
        ),
    ],
    [S("Seguimiento específico",
       C("permeabilidad", "Permeabilidad del injerto", "radio",
         ["Permeable (primaria)", "Permeable (primaria asistida)", "Permeable (secundaria)", "Ocluido"], req=True),
       C("estenosis_injerto", "Estenosis > 50 % en el eco-doppler", "sino"),
       C("infeccion_injerto", "Infección del injerto", "sino"),
       *SEGUIMIENTO_EXTREMIDAD)],
)

# Endovascular periférico ----------------------------------------------------
procedimiento(
    "endo_periferico", "Endovascular periférico",
    "Angioplastia, stent, aterectomía, litotricia y otras técnicas en miembros inferiores.",
    [
        S(
            "Indicación y lesión",
            C("indicacion", "Indicación", "select", INDICACION_PERIFERICA, req=True),
            C("lado", "Lado", "radio", LADO, req=True),
            C("rutherford", "Rutherford", "select", RUTHERFORD),
            *WIFI,
            C("sectores", "Sectores tratados", "multi", [
                "Aortoilíaco", "Femoral común", "Femoropoplíteo", "Infrapoplíteo", "Pie (inframaleolar)",
            ], req=True),
            C("tipo_lesion", "Tipo de lesión", "radio", ["Estenosis", "Oclusión", "Ambas"]),
            C("longitud_lesion_mm", "Longitud total de la lesión", "numero", min=0, max=600, unidad="mm"),
            C("tasc", "TASC II", "select", ["A", "B", "C", "D"]),
            C("glass", "GLASS", "select", ["I", "II", "III"]),
            C("calcificacion", "Calcificación (PACSS)", "select", ["0", "1", "2", "3", "4"]),
        ),
        S(
            "Técnica",
            C("acceso", "Acceso", "multi", [
                "Femoral anterógrado", "Femoral retrógrado (crossover)", "Braquial/radial",
                "Tibiopedio retrógrado",
            ], req=True),
            C("recanalizacion", "Recanalización", "radio", ["Intraluminal", "Subintimal", "No aplica"]),
            C("tecnicas", "Técnicas empleadas", "multi", [
                "Angioplastia simple", "Balón farmacoactivo", "Balón de corte/scoring",
                "Stent metálico desnudo", "Stent farmacoactivo", "Stent cubierto", "Aterectomía",
                "Litotricia intravascular", "Trombectomía/aspiración", "Fibrinólisis",
            ], req=True),
            C("cierre", "Cierre del acceso", "select", ["Compresión manual", "Dispositivo de cierre", "Quirúrgico"]),
        ),
    ],
    [S("Seguimiento específico",
       C("permeabilidad", "Permeabilidad del segmento tratado", "radio",
         ["Permeable", "Reestenosis > 50 %", "Ocluido", "No valorada"], req=True),
       C("tlr", "Revascularización de la lesión diana (TLR)", "sino"),
       *SEGUIMIENTO_EXTREMIDAD)],
)

# Acceso vascular ------------------------------------------------------------
_creacion = [
    "FAV radiocefálica (muñeca)", "FAV radiocefálica (tabaquera)", "FAV humerocefálica",
    "FAV humerobasílica en un tiempo", "FAV humerobasílica en dos tiempos",
    "Prótesis (PTFE) en brazo/antebrazo", "Prótesis en muslo",
]
procedimiento(
    "acceso_vascular", "Acceso vascular",
    "Creación, mantenimiento y rescate de accesos para hemodiálisis.",
    [
        S(
            "Situación previa",
            C("situacion_dialisis", "Situación", "select", [
                "Prediálisis", "Hemodiálisis por catéter", "Hemodiálisis por FAV previa",
                "Diálisis peritoneal",
            ], req=True),
            C("accesos_previos", "Número de accesos previos", "numero", min=0, max=30),
            C("lado", "Lado", "radio", ["Derecho", "Izquierdo"], req=True),
        ),
        S(
            "Procedimiento",
            C("tipo_procedimiento", "Procedimiento", "select", _creacion + [
                "Superficialización/transposición (2.º tiempo)", "Rescate quirúrgico de FAV",
                "Angioplastia de FAV", "Trombectomía de FAV", "Ligadura/cierre de FAV",
                "Cirugía de robo (DRIL, banding…)", "Otro",
            ], req=True),
            C("diametro_arteria_mm", "Diámetro de la arteria", "numero", min=0, max=15, unidad="mm",
              si=si("tipo_procedimiento", *_creacion)),
            C("diametro_vena_mm", "Diámetro de la vena", "numero", min=0, max=15, unidad="mm",
              si=si("tipo_procedimiento", *_creacion)),
            C("thrill_final", "Thrill al final de la intervención", "sino"),
        ),
    ],
    [S("Seguimiento específico",
       C("estado_acceso", "Estado del acceso", "select", [
           "Funcionante en uso", "Madurando", "Madurado sin usar", "Fallo de maduración",
           "Trombosado", "Abandonado/ligado",
       ], req=True),
       C("fecha_primera_puncion", "Fecha de la primera punción", "fecha"),
       C("flujo_ml_min", "Flujo del acceso", "numero", min=0, max=5000, unidad="ml/min"),
       C("intervenciones_mantenimiento", "Intervenciones de mantenimiento desde la última revisión",
         "numero", min=0, max=50),
       C("complicaciones_acceso", "Complicaciones", "multi", [
           "Ninguna", "Síndrome de robo", "Hiperaflujo/insuficiencia cardiaca", "Infección",
           "Aneurisma/pseudoaneurisma", "Estenosis venosa central",
       ]))],
)

# Ramas viscerales -----------------------------------------------------------
_bypass_visceral = ["Bypass anterógrado (aorta supracelíaca)", "Bypass retrógrado (ilíaco/aórtico)"]
procedimiento(
    "viscerales", "Ramas viscerales",
    "Isquemia mesentérica aguda y crónica, aneurismas viscerales y otras patologías de ramas viscerales.",
    [
        S(
            "Indicación",
            C("patologia", "Patología", "select", [
                "Isquemia mesentérica aguda", "Isquemia mesentérica crónica",
                "Aneurisma de arteria visceral", "Estenosis/aneurisma de arteria renal",
                "Compresión por ligamento arcuato medio", "Disección visceral aislada", "Otra",
            ], req=True),
            C("etiologia_ima", "Etiología", "select", [
                "Embólica", "Trombótica", "No oclusiva", "Trombosis venosa mesentérica",
            ], si=si("patologia", "Isquemia mesentérica aguda"), req=True),
            C("horas_sintomas", "Tiempo desde el inicio de los síntomas", "numero", min=0, max=720,
              unidad="h", si=si("patologia", "Isquemia mesentérica aguda")),
            C("lactato", "Lactato preoperatorio", "numero", min=0, max=30, unidad="mmol/l",
              si=si("patologia", "Isquemia mesentérica aguda")),
            C("perdida_peso_kg", "Pérdida de peso previa", "numero", min=0, max=80, unidad="kg",
              si=si("patologia", "Isquemia mesentérica crónica")),
            C("vasos_afectados", "Vasos afectados", "multi", [
                "Tronco celíaco", "AMS", "AMI", "Renal derecha", "Renal izquierda", "Esplénica",
                "Hepática", "Otra",
            ], req=True),
            C("diametro_aneurisma_mm", "Diámetro del aneurisma", "numero", min=0, max=150, unidad="mm",
              si=si("patologia", "Aneurisma de arteria visceral", "Estenosis/aneurisma de arteria renal")),
        ),
        S(
            "Técnica",
            C("tecnica", "Técnica", "multi", [
                "Embolectomía de AMS", "Endarterectomía", *_bypass_visceral,
                "Stent anterógrado (femoral/braquial)", "Stent retrógrado abierto (ROMS)",
                "Trombectomía/fibrinólisis endovascular", "Embolización (coils/plug)", "Stent cubierto",
                "Resección/ligadura de aneurisma", "Liberación del ligamento arcuato", "Otra",
            ], req=True),
            C("conducto", "Conducto del bypass", "radio", ["Vena safena", "Prótesis"],
              si=si("tecnica", *_bypass_visceral)),
            C("laparotomia", "Laparotomía exploradora", "sino",
              si=si("patologia", "Isquemia mesentérica aguda")),
            C("reseccion_intestinal", "Resección intestinal", "sino", si=si("laparotomia", "Sí")),
            C("longitud_reseccion_cm", "Longitud resecada", "numero", min=0, max=800, unidad="cm",
              si=si("reseccion_intestinal", "Sí")),
            C("second_look", "Second look", "sino", si=si("laparotomia", "Sí")),
        ),
    ],
    [S("Seguimiento específico",
       C("permeabilidad", "Permeabilidad del vaso tratado", "radio",
         ["Permeable", "Reestenosis > 50 %", "Ocluido", "No valorada"]),
       C("recurrencia_sintomas", "Recurrencia de síntomas", "sino"),
       C("peso_kg", "Peso actual", "numero", min=20, max=250, unidad="kg"),
       C("nutricion_parenteral", "Nutrición parenteral", "sino"),
       C("intestino_corto", "Síndrome de intestino corto", "sino"))],
)

# Carótida -------------------------------------------------------------------
_sintomaticas = ["Sintomática: AIT", "Sintomática: amaurosis fugax", "Sintomática: ictus menor",
                 "Sintomática: ictus establecido"]
procedimiento(
    "carotida", "Carótida",
    "Revascularización carotídea abierta (endarterectomía) o endovascular (CAS, TCAR).",
    [
        S(
            "Indicación",
            C("sintomatologia", "Sintomatología", "select", ["Asintomática"] + _sintomaticas, req=True),
            C("dias_desde_sintoma", "Días desde el último evento", "numero", min=0, max=365,
              si=si("sintomatologia", *_sintomaticas)),
            C("lado", "Lado", "radio", ["Derecho", "Izquierdo"], req=True),
            C("estenosis", "Grado de estenosis (NASCET)", "select",
              ["50-69 %", "70-99 %", "Suboclusión (near-occlusion)", "Reestenosis"], req=True),
            C("contralateral", "Carótida contralateral", "select", ["< 50 %", "50-69 %", "70-99 %", "Ocluida"]),
            C("rankin_preop", "Rankin modificado previo", "select", ["0", "1", "2", "3", "4", "5"]),
        ),
        S(
            "Técnica",
            C("abordaje", "Abordaje", "radio", ["Abierto", "Endovascular"], req=True),
            C("tecnica_abierta", "Técnica", "select", [
                "Endarterectomía convencional con parche", "Endarterectomía convencional con cierre primario",
                "Endarterectomía por eversión", "Bypass/interposición",
            ], si=si("abordaje", "Abierto"), req=True),
            C("parche", "Parche", "select", ["Dacron", "PTFE", "Pericardio bovino", "Vena"],
              si=si("tecnica_abierta", "Endarterectomía convencional con parche")),
            C("shunt", "Shunt", "radio", ["No", "Sí, sistemático", "Sí, selectivo"], si=si("abordaje", "Abierto")),
            C("monitorizacion", "Monitorización neurológica", "multi", [
                "Paciente despierto", "NIRS", "Presión de reflujo (stump pressure)",
                "Doppler transcraneal", "EEG/potenciales evocados", "Ninguna",
            ], si=si("abordaje", "Abierto")),
            C("tecnica_endo", "Técnica", "select", [
                "CAS transfemoral", "TCAR (transcarotídeo con inversión de flujo)", "CAS transradial/braquial",
            ], si=si("abordaje", "Endovascular"), req=True),
            C("proteccion_embolica", "Protección embólica", "select",
              ["Filtro distal", "Oclusión proximal/inversión de flujo", "Sin protección"],
              si=si("abordaje", "Endovascular")),
            C("stent", "Tipo de stent", "select", ["Celda abierta", "Celda cerrada", "Doble malla"],
              si=si("abordaje", "Endovascular")),
            C("complicaciones_carotida", "Complicaciones específicas", "multi", [
                "Ninguna", "Ictus homolateral", "Síndrome de hiperperfusión", "Bradicardia/hipotensión",
                "Lesión de nervio craneal", "Hematoma cervical",
            ]),
        ),
    ],
    [S("Seguimiento específico",
       C("ictus_homolateral", "Ictus homolateral", "sino", req=True),
       C("ictus_contralateral", "Ictus contralateral", "sino"),
       C("ait", "AIT", "sino"),
       C("reestenosis", "Reestenosis en el eco-doppler", "select",
         ["< 50 %", "50-69 %", "≥ 70 %", "Oclusión", "No valorada"]),
       C("lesion_nervio", "Lesión de nervio craneal persistente", "sino"),
       C("rankin", "Rankin modificado", "select", ["0", "1", "2", "3", "4", "5", "6"]))],
)

# Congestión venosa pélvica --------------------------------------------------
procedimiento(
    "congestion_pelvica", "Congestión venosa pélvica",
    "Síndrome de congestión pélvica, Nutcracker, compresión ilíaca y varices de origen pélvico.",
    [
        S(
            "Diagnóstico",
            C("diagnostico", "Diagnóstico", "multi", [
                "Insuficiencia de venas gonadales/hipogástricas", "Síndrome de Nutcracker",
                "Compresión ilíaca (May-Thurner)", "Varices vulvares/perineales de origen pélvico",
            ], req=True),
            C("sintomas", "Síntomas", "multi", [
                "Dolor pélvico crónico", "Dispareunia", "Dolor postcoital",
                "Varices vulvares/perineales", "Varices atípicas en MMII", "Hematuria",
                "Síntomas urinarios",
            ]),
            C("eva_basal", "Dolor pélvico basal (EVA 0-10)", "numero", min=0, max=10),
            C("gestaciones", "Número de gestaciones", "numero", min=0, max=20),
            C("pruebas", "Pruebas diagnósticas", "multi", [
                "Eco-doppler transvaginal", "Eco-doppler abdominal", "AngioTC", "AngioRM",
                "Flebografía", "IVUS",
            ]),
        ),
        S(
            "Técnica",
            C("acceso", "Acceso venoso", "radio", ["Yugular", "Femoral", "Braquial", "Quirúrgico"]),
            C("venas_tratadas", "Venas tratadas", "multi", [
                "Ovárica izquierda", "Ovárica derecha", "Hipogástrica izquierda", "Hipogástrica derecha",
                "Vena renal izquierda", "Ilíaca común izquierda", "Otra",
            ], req=True),
            C("tecnica", "Técnica", "multi", [
                "Coils", "Plug", "Espuma esclerosante", "Cianoacrilato", "Stent venoso",
                "Transposición de vena renal izquierda", "Otra",
            ], req=True),
        ),
    ],
    [S("Seguimiento específico",
       C("eva", "Dolor pélvico actual (EVA 0-10)", "numero", min=0, max=10, req=True),
       C("dispareunia", "Dispareunia", "select", ["No aplica", "Resuelta", "Mejorada", "Igual", "Peor"]),
       C("pgic", "Impresión global de cambio (PGIC)", "select",
         ["Mucho mejor", "Mejor", "Algo mejor", "Igual", "Peor"]),
       C("recurrencia_varices", "Recurrencia de varices pélvicas/vulvares", "sino"),
       C("migracion_coils", "Migración de coils/plug", "sino"),
       C("trombosis_stent", "Trombosis del stent venoso", "sino"))],
)

# Varices --------------------------------------------------------------------
procedimiento(
    "varices", "Varices",
    "Tratamiento de la insuficiencia venosa superficial de miembros inferiores.",
    [
        S(
            "Clínica (CEAP)",
            C("lado", "Lado", "radio", LADO, req=True),
            C("ceap_c", "CEAP - Clínica (C)", "select",
              ["C1", "C2", "C3", "C4a", "C4b", "C4c", "C5", "C6"], req=True),
            C("ceap_e", "CEAP - Etiología (E)", "radio", ["Primaria", "Secundaria", "Congénita"]),
            C("ceap_a", "CEAP - Anatomía (A)", "multi", ["Superficial", "Profundo", "Perforantes"]),
            C("ceap_p", "CEAP - Fisiopatología (P)", "radio", ["Reflujo", "Obstrucción", "Ambos"]),
            C("vcss", "VCSS", "numero", min=0, max=30),
            C("recidiva", "Varices recidivadas", "sino"),
        ),
        S(
            "Técnica",
            C("ejes", "Ejes tratados", "multi", [
                "Safena mayor", "Safena menor", "Safena accesoria anterior", "Perforantes",
                "Tributarias",
            ], req=True),
            C("diametro_vena_mm", "Diámetro máximo del eje", "numero", min=0, max=30, unidad="mm"),
            C("tecnica", "Técnica", "multi", [
                "Crosectomía + stripping", "Láser endovenoso", "Radiofrecuencia", "Cianoacrilato",
                "Ablación mecanoquímica (MOCA)", "Espuma ecoguiada", "Flebectomías",
                "CHIVA", "ASVAL", "Cirugía de perforantes",
            ], req=True),
            C("ambulatoria", "Cirugía ambulatoria", "sino"),
        ),
    ],
    [S("Seguimiento específico",
       C("oclusion_eje", "Oclusión del eje tratado", "select",
         ["No aplica", "Oclusión completa", "Recanalización parcial", "Recanalización completa"]),
       C("recurrencia", "Recurrencia", "radio", ["No", "Sí, clínica", "Sí, solo ecográfica"]),
       C("vcss", "VCSS", "numero", min=0, max=30),
       C("complicaciones_venosas", "Complicaciones", "multi", [
           "Ninguna", "TVP", "EHIT/ETIT", "Tromboflebitis superficial", "Parestesias/lesión nerviosa",
           "Hiperpigmentación", "Quemadura cutánea",
       ]),
       C("ulcera", "Úlcera venosa", "select", ["No aplica", "Cicatrizada", "Abierta", "Recidivada"]),
       C("satisfaccion", "Satisfacción del paciente (0-10)", "numero", min=0, max=10))],
)

# Misceláneos ----------------------------------------------------------------
procedimiento(
    "miscelanea", "Misceláneos",
    "Cualquier procedimiento que no encaje en los grupos anteriores.",
    [
        S(
            "Procedimiento",
            C("categoria", "Categoría", "select", [
                "Amputación mayor", "Amputación menor", "Trauma vascular",
                "Embolectomía/trombectomía aislada", "Fasciotomía", "Aneurisma periférico (no poplíteo)",
                "Síndrome del opérculo torácico", "Malformación vascular", "Trombectomía venosa profunda",
                "Filtro de vena cava", "Infección protésica", "Otra",
            ], req=True),
            C("lado", "Lado", "radio", LADO + ["No aplica"]),
            C("descripcion", "Descripción del procedimiento", "area", req=True),
        ),
    ],
    [S("Seguimiento específico",
       C("resultado", "Resultado del procedimiento", "area"))],
)


# ---------------------------------------------------------------------------
# Hitos de seguimiento
# ---------------------------------------------------------------------------

HITOS = [
    ("1m", 30, "1 mes"),
    ("3m", 90, "3 meses"),
    ("6m", 180, "6 meses"),
    ("12m", 365, "1 año"),
]
ETIQUETA_HITO = {clave: etiqueta for clave, _, etiqueta in HITOS}


# ---------------------------------------------------------------------------
# Acceso a los formularios
# ---------------------------------------------------------------------------

def formulario_cirugia(tipo):
    p = PROCEDIMIENTOS[tipo]
    return COMUN_PREOPERATORIO + p["secciones"] + [COMUN_INTRAOPERATORIO] + COMUN_POSTOPERATORIO


def formulario_seguimiento(tipo):
    return COMUN_SEGUIMIENTO + PROCEDIMIENTOS[tipo]["seguimiento"]


def campos(secciones):
    for seccion in secciones:
        yield from seccion["campos"]


def visible(campo, datos):
    condiciones = campo.get("si")
    if condiciones is None:
        return True
    if isinstance(condiciones, dict):
        condiciones = [condiciones]
    for cond in condiciones:
        valor = datos.get(cond["campo"])
        if valor in (None, "", []):
            return False
        valores = valor if isinstance(valor, list) else [valor]
        if "valores" in cond and not set(valores) & set(cond["valores"]):
            return False
        if "excepto" in cond and set(valores) <= set(cond["excepto"]):
            return False
    return True


def procesar(secciones, form):
    """Valida un formulario enviado (MultiDict) y devuelve (datos, errores).

    Los campos ocultos por su condición se descartan aunque lleguen con valor.
    """
    datos, errores = {}, {}
    for c in campos(secciones):
        if not visible(c, datos):
            continue
        nombre, tipo = c["nombre"], c["tipo"]
        if tipo == "multi":
            valor = [v for v in form.getlist(nombre) if v in c["opciones"]]
        else:
            valor = (form.get(nombre) or "").strip()
            if tipo in ("select", "radio", "sino") and valor and valor not in c["opciones"]:
                errores[nombre] = "Opción no válida."
                continue
            if tipo == "numero" and valor:
                try:
                    numero = float(valor.replace(",", "."))
                except ValueError:
                    errores[nombre] = "Debe ser un número."
                    continue
                if "min" in c and numero < c["min"] or "max" in c and numero > c["max"]:
                    errores[nombre] = f"Debe estar entre {c.get('min', '-∞')} y {c.get('max', '∞')}."
                    continue
                valor = int(numero) if numero.is_integer() else numero
            if tipo == "fecha" and valor and not _fecha_valida(valor):
                errores[nombre] = "Fecha no válida."
                continue
        if valor in ("", []):
            if c["req"]:
                errores[nombre] = "Campo obligatorio."
            continue
        datos[nombre] = valor
    return datos, errores


def _fecha_valida(texto):
    from datetime import date
    try:
        date.fromisoformat(texto)
        return True
    except ValueError:
        return False


def valor_legible(valor):
    if isinstance(valor, list):
        return " | ".join(str(v) for v in valor)
    return "" if valor is None else str(valor)
