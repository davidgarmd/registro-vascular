"""Definición de los formularios dinámicos del registro.

Cada formulario es una lista de secciones; cada sección tiene un título y una
lista de campos. Un campo es un diccionario con:

    nombre     identificador interno (único dentro del formulario)
    etiqueta   texto que ve el usuario
    tipo       texto | area | numero | fecha | select | radio | multi | sino | dispositivos | calculado
               (dispositivos = lista de filas: tipo, vaso, marca/modelo, diámetro y longitud)
    opciones   lista de valores (select, radio, multi)
    req        obligatorio cuando el campo está visible
    si         condición de visibilidad: {"campo": x, "valores": [...]}
               o {"campo": x, "excepto": [...]}; admite una lista (todas deben cumplirse).
               Solo puede referirse a campos anteriores del mismo formulario.
    min, max   límites para campos numéricos
    unidad     texto que se muestra tras un campo numérico
    ayuda      aclaración breve
    guia       lista de (valor, descripción) de una escala; la descripción se muestra junto a
               cada opción («IIIb · Requiere…») y se guarda solo el valor (queda en «descripciones»)
    calculado  campo que se rellena solo a partir de otros (se usa el primer término de cada
               respuesta; p. ej. «2 · …» → «2»). Reglas:
                 {"entradas": [a, b], "tabla": {"a|b": valor}}      búsqueda en tabla
                 {"suma": [a, b, …]}                                suma de puntos
                 {"entradas": [total], "rangos": [[hasta, texto]…],
                  "forzar": {"campo": x, "valor": v, "texto": t}}   interpretación de un total
                 {"svp": True}                                      código SVP

Para añadir o cambiar variables basta con editar este fichero: los datos se
guardan como JSON, así que no hace falta tocar la base de datos.
"""

from . import escalas as E

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
    guia = dict(extra.pop("guia", None) or [])
    if guia and opciones:
        descripciones = {op: guia.get(op) or guia.get(op.split(" ")[0]) for op in campo["opciones"]}
        campo["descripciones"] = {op: d for op, d in descripciones.items() if d}
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
        C("asa", "ASA", "select", ["I", "II", "III", "IV", "V"], guia=E.ASA),
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

EXITUS_HOSPITALARIO = "Exitus hospitalario"

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
        C("reint_ingreso_fecha", "Fecha de la reintervención", "fecha", si=si("reintervencion_ingreso", "Sí"),
          req=True),
        C("reint_ingreso_motivo", "Motivo de la reintervención", "select", [
            "Hemorragia/hematoma", "Trombosis/oclusión", "Isquemia persistente", "Infección de herida",
            "Síndrome compartimental", "Isquemia intestinal", "Complicación del acceso", "Endofuga", "Otra",
        ], si=si("reintervencion_ingreso", "Sí"), req=True),
        C("reint_ingreso_via", "Vía", "radio", ["Abierta", "Endovascular", "Híbrida"],
          si=si("reintervencion_ingreso", "Sí"), req=True),
        C("reint_ingreso_detalle", "Qué se hizo", "area", si=si("reintervencion_ingreso", "Sí"),
          ayuda="Si es una intervención relevante (p. ej., un nuevo bypass), regístrala además con "
                "«+ Reintervención» para tener su formulario completo."),
        C("clavien_dindo", "Clavien-Dindo (peor complicación)", "select",
          ["0 (sin complicaciones)", "I", "II", "IIIa", "IIIb", "IVa", "IVb", "V"], guia=E.CLAVIEN_DINDO),
        C("estancia_uci_dias", "Estancia en UCI/REA", "numero", min=0, max=365, unidad="días"),
        C("estancia_dias", "Estancia hospitalaria total", "numero", min=0, max=365, unidad="días"),
        C("destino_alta", "Destino al alta", "select", [
            "Domicilio", "Centro sociosanitario", "Traslado a otro hospital", EXITUS_HOSPITALARIO,
        ]),
        C("fecha_exitus", "Fecha del exitus", "fecha", si=si("destino_alta", EXITUS_HOSPITALARIO), req=True),
        C("causa_exitus", "Causa del exitus", "select", [
            "Relacionada con el procedimiento", "Cardiovascular", "Fallo multiorgánico/sepsis", "Otra causa",
            "Desconocida",
        ], si=si("destino_alta", EXITUS_HOSPITALARIO), req=True),
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
        C("fecha_fallecimiento", "Fecha de fallecimiento", "fecha", si=si("estado_vital", "Fallecido"),
          req=True),
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

TIPOS_DISPOSITIVO = [
    "Balón", "Balón farmacoactivo", "Balón de corte/scoring",
    "Stent autoexpandible", "Stent balón-expandible", "Stent farmacoactivo",
    "Stent cubierto autoexpandible", "Stent cubierto balón-expandible", "Stent venoso",
    "Endoprótesis aórtica (cuerpo principal)", "Endoprótesis (rama/extensión/cuff)",
    "Rama ilíaca (IBE)", "Coil", "Plug", "Dispositivo de cierre", "Otro",
]
TECNICAS_ENDO_PERIFERICAS = [
    "Angioplastia simple", "Balón farmacoactivo", "Balón de corte/scoring",
    "Stent metálico desnudo", "Stent farmacoactivo", "Stent cubierto", "Aterectomía",
    "Litotricia intravascular", "Trombectomía/aspiración", "Fibrinólisis",
]
PIE_DIABETICO_SIN_ISQUEMIA = "Pie diabético sin isquemia (infeccioso/neuropático)"
AMPUTACION_SEGUIMIENTO = C(
    "amputacion", "Amputación desde la última revisión", "radio",
    ["No", "Digital", "Transmetatarsiana", "Infracondílea", "Supracondílea"])


_CLTI = ["Isquemia crónica: dolor en reposo", "Isquemia crónica: lesión trófica", "Rescate de bypass/stent previo"]


def glass():
    """GLASS: grados femoropoplíteo e infrapoplíteo → estadio calculado (solo en isquemia crónica amenazante)."""
    cond = si("indicacion", *_CLTI)
    return [
        C("glass_fp", "GLASS - Segmento femoropoplíteo", "radio", E.GLASS_FP, si=cond, ayuda=E.AYUDA_GLASS),
        C("glass_ip", "GLASS - Segmento infrapoplíteo (arteria diana)", "radio", E.GLASS_IP, si=cond),
        C("glass", "Estadio GLASS", "calculado", si=cond,
          calculado={"entradas": ["glass_fp", "glass_ip"], "tabla": E.TABLA_GLASS}),
        C("glass_inframaleolar", "GLASS - Modificador inframaleolar", "radio", E.GLASS_IM, si=cond),
        C("glass_entrada", "Enfermedad de entrada (aortoilíaca) significativa", "sino", si=cond),
    ]


def material(si=None):
    """Material implantado con medidas + descripción libre del procedimiento endovascular."""
    return [
        C("dispositivos", "Material utilizado (con medidas)", "dispositivos", si=si,
          ayuda="Añade una fila por dispositivo. Diámetro y longitud en mm."),
        C("material_detalle", "Descripción del procedimiento endovascular / material", "area", si=si),
    ]
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
_WIFI_SI = si("indicacion", "Isquemia crónica: dolor en reposo", "Isquemia crónica: lesión trófica")
WIFI = [
    C("wifi_w", "WIfI - Herida (W)", "select", ["0", "1", "2", "3"], guia=E.WIFI_W, si=_WIFI_SI),
    C("wifi_i", "WIfI - Isquemia (I)", "select", ["0", "1", "2", "3"], guia=E.WIFI_I, si=_WIFI_SI),
    C("wifi_fi", "WIfI - Infección del pie (fI)", "select", ["0", "1", "2", "3"], guia=E.WIFI_FI, si=_WIFI_SI),
    C("wifi", "Estadio clínico WIfI", "calculado", si=_WIFI_SI,
      calculado={"entradas": ["wifi_w", "wifi_i", "wifi_fi"], "tabla": E.TABLA_WIFI},
      ayuda="Riesgo de amputación al año. El estadio 5 (pie no salvable) es un juicio clínico."),
]
SEGUIMIENTO_EXTREMIDAD = [
    C("rutherford_actual", "Rutherford actual", "select", RUTHERFORD),
    C("itb", "Índice tobillo-brazo", "numero", min=0, max=3, ayuda="Usa punto decimal: 0.85"),
    AMPUTACION_SEGUIMIENTO,
    C("cicatrizacion", "Lesión trófica", "select",
      ["No aplica", "Cicatrizada", "En proceso de cicatrización", "Sin cambios", "Empeora"]),
]
SEGUIMIENTO_AORTA_ENDO = [
    C("diametro_saco_mm", "Diámetro máximo del saco", "numero", min=0, max=150, unidad="mm"),
    C("evolucion_saco", "Evolución del saco", "radio",
      ["Regresión ≥ 5 mm", "Estable", "Crecimiento ≥ 5 mm", "No valorable"]),
    C("endofuga", "Endofuga", "multi", ENDOFUGAS + ["Endotensión (tipo V)", "No valorable"], guia=E.ENDOFUGAS),
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

def villalta():
    """Escala de Villalta: 11 elementos + úlcera → total (0-33) y gravedad calculados."""
    items = [C(f"villalta_{k}", texto, "select", [v for v, _ in E.VILLALTA_INTENSIDAD],
               guia=E.VILLALTA_INTENSIDAD) for k, texto in E.VILLALTA_ITEMS]
    return [
        *items,
        C("villalta_ulcera", "Úlcera venosa", "sino"),
        C("villalta", "Villalta (puntos)", "calculado", calculado={"suma": [c["nombre"] for c in items]}),
        C("villalta_grado", "Gravedad del síndrome postrombótico", "calculado",
          calculado={"entradas": ["villalta"], "rangos": E.VILLALTA_GRADOS,
                     "forzar": {"campo": "villalta_ulcera", "valor": "Sí",
                                "texto": E.VILLALTA_GRAVE_POR_ULCERA}}),
    ]


def vcss():
    """VCSS revisado: 10 elementos de 0 a 3 → total calculado (0-30)."""
    items = [C(f"vcss_{k}", texto, "select", [v for v, _ in niveles], guia=niveles)
             for k, texto, niveles in E.VCSS_ITEMS]
    return [*items, C("vcss", "VCSS (puntos)", "calculado", calculado={"suma": [c["nombre"] for c in items]})]


def svp():
    """Clasificación SVP de los trastornos venosos pélvicos → código calculado."""
    anatomia = [v for v, _ in E.SVP_ANATOMIA]
    return [
        C("svp_s", "SVP - Síntomas (S)", "multi", [v for v, _ in E.SVP_S], guia=E.SVP_S),
        C("svp_v", "SVP - Varices (V)", "multi", [v for v, _ in E.SVP_V], guia=E.SVP_V),
        C("svp_anatomia", "SVP - Segmentos venosos afectados (P, anatomía)", "multi", anatomia,
          guia=E.SVP_ANATOMIA),
        *[C(f"svp_h_{seg}", f"Hemodinámica en {seg} ({desc.lower()})", "radio",
            [v for v, _ in E.SVP_HEMODINAMICA], guia=E.SVP_HEMODINAMICA, si=si("svp_anatomia", seg))
          for seg, desc in E.SVP_ANATOMIA],
        C("svp_etiologia", "SVP - Etiología (P)", "radio", [v for v, _ in E.SVP_ETIOLOGIA],
          guia=E.SVP_ETIOLOGIA),
        C("svp", "Código SVP", "calculado", calculado={"svp": True}),
    ]


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
            C("crawford", "Clasificación de Crawford", "select", ["I", "II", "III", "IV", "V"], guia=E.CRAWFORD,
              si=si("extension", "Toracoabdominal")),
            C("tasc_aortoiliaco", "TASC II aortoilíaco", "select", ["A", "B", "C", "D"],
              guia=E.TASC_AORTOILIACO,
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
            C("endofuga_final", "Endofuga en la angiografía final", "multi", ENDOFUGAS, req=True,
              guia=E.ENDOFUGAS),
            *material(),
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
              si=si("patologia", *_disecciones), guia=E.DISECCION_TIPO_B),
            C("presentacion", "Presentación", "radio", ["Asintomático", "Sintomático", "Roto"]),
            C("diametro_max_mm", "Diámetro máximo", "numero", min=0, max=150, unidad="mm"),
        ),
        S(
            "Técnica",
            C("variante", "Variante", "radio", [
                "TEVAR estándar", "TEVAR con rama para subclavia izquierda",
                "TEVAR con ramas/fenestraciones para troncos supraaórticos", "TEVAR + debranching quirúrgico",
            ], req=True),
            C("zona_proximal", "Zona de anclaje proximal (Ishimaru)", "select", ["0", "1", "2", "3", "4"],
              req=True, guia=E.ISHIMARU),
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
            C("endofuga_final", "Endofuga en la angiografía final", "multi", ENDOFUGAS, req=True,
              guia=E.ENDOFUGAS),
            *material(),
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
              si=si("indicacion", "Isquemia aguda"), guia=E.RUTHERFORD_AGUDA),
            *glass(),
            C("pie_diabetico", "Pie diabético", "sino"),
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
            C("profundoplastia", "Profundoplastia (plastia de femoral profunda)", "sino"),
            C("amputacion_menor_asociada", "Amputación menor/desbridamiento asociado", "sino"),
        ),
        S(
            "Procedimiento híbrido",
            C("hibrido", "Tratamiento endovascular asociado (híbrido)", "sino", req=True),
            C("sector_hibrido", "Sector tratado por vía endovascular", "multi", [
                "Aortoilíaco (entrada)", "Femoral superficial/poplítea", "Troncos distales (salida)",
            ], si=si("hibrido", "Sí"), req=True),
            C("tecnicas_hibrido", "Técnica endovascular", "multi", TECNICAS_ENDO_PERIFERICAS,
              si=si("hibrido", "Sí"), req=True),
            *material(si=si("hibrido", "Sí")),
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
            C("tasc_aortoiliaco", "TASC II aortoilíaco", "select", ["A", "B", "C", "D"],
              si=si("sectores", "Aortoilíaco"), guia=E.TASC_AORTOILIACO),
            C("tasc_femoropopliteo", "TASC II femoropoplíteo", "select", ["A", "B", "C", "D"],
              si=si("sectores", "Femoral común", "Femoropoplíteo"), guia=E.TASC_FEMOROPOPLITEO),
            *glass(),
            C("calcificacion", "Calcificación (PACSS)", "select", ["0", "1", "2", "3", "4"], guia=E.PACSS),
            C("pie_diabetico", "Pie diabético", "sino"),
        ),
        S(
            "Técnica",
            C("acceso", "Acceso", "multi", [
                "Femoral anterógrado", "Femoral retrógrado (crossover)", "Braquial/radial",
                "Tibiopedio retrógrado",
            ], req=True),
            C("recanalizacion", "Recanalización", "radio", ["Intraluminal", "Subintimal", "No aplica"]),
            C("tecnicas", "Técnicas empleadas", "multi", TECNICAS_ENDO_PERIFERICAS, req=True),
            C("cierre", "Cierre del acceso", "select", ["Compresión manual", "Dispositivo de cierre", "Quirúrgico"]),
            *material(),
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
_PRIMARIA = "Primaria (acceso nuevo)"
_SECUNDARIA = "Secundaria (complicación de un acceso existente)"
_RESECCION_INFECCION = "Resección del segmento infectado + interposición de injerto"
_RESECCION_ANEURISMA = "Resección + interposición de injerto"
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
            C("cirugia", "Tipo de cirugía", "radio", [_PRIMARIA, _SECUNDARIA], req=True),
            C("tipo_procedimiento", "Acceso creado", "select", _creacion + [
                "Superficialización/transposición (2.º tiempo)", "Otro",
            ], si=si("cirugia", _PRIMARIA), req=True),
            C("diametro_arteria_mm", "Diámetro de la arteria", "numero", min=0, max=15, unidad="mm",
              si=si("cirugia", _PRIMARIA)),
            C("diametro_vena_mm", "Diámetro de la vena", "numero", min=0, max=15, unidad="mm",
              si=si("cirugia", _PRIMARIA)),
            C("acceso_afectado", "Acceso afectado", "select", [
                "FAV radiocefálica", "FAV humerocefálica", "FAV humerobasílica",
                "Prótesis en brazo/antebrazo", "Prótesis en muslo", "Otro",
            ], si=si("cirugia", _SECUNDARIA), req=True),
            C("complicacion_acceso", "Complicación que motiva la cirugía", "select", [
                "Infección", "Degeneración aneurismática", "Pseudoaneurisma", "Síndrome de robo",
                "Hiperaflujo", "Trombosis", "Estenosis/disfunción", "Otra",
            ], si=si("cirugia", _SECUNDARIA), req=True),
            C("tecnica_infeccion", "Técnica", "select", [
                "Cierre/ligadura de la FAV", _RESECCION_INFECCION,
                "Resección del segmento infectado + bypass de rodeo", "Explante completo de la prótesis",
                "Otra",
            ], si=si("complicacion_acceso", "Infección"), req=True),
            C("injerto_infeccion", "Injerto de interposición", "radio", ["Venoso", "Protésico"],
              si=si("tecnica_infeccion", _RESECCION_INFECCION)),
            C("tecnica_aneurisma", "Técnica", "select", [
                "Resección + plastia (aneurismorrafia)", _RESECCION_ANEURISMA,
                "Cierre/ligadura de la FAV", "Exclusión con stent cubierto", "Otra",
            ], si=si("complicacion_acceso", "Degeneración aneurismática", "Pseudoaneurisma"), req=True),
            C("injerto_aneurisma", "Injerto de interposición", "radio", ["Venoso", "Protésico"],
              si=si("tecnica_aneurisma", _RESECCION_ANEURISMA)),
            C("tecnica_robo", "Técnica", "select", [
                "DRIL", "RUDI", "PAI (proximalización del flujo arterial)", "Banding",
                "Cierre/ligadura de la FAV", "Otra",
            ], si=si("complicacion_acceso", "Síndrome de robo"), req=True),
            C("tecnica_hiperaflujo", "Técnica", "select", [
                "Banding / MILLER", "RUDI", "Cierre/ligadura de la FAV", "Otra",
            ], si=si("complicacion_acceso", "Hiperaflujo"), req=True),
            C("tecnica_trombosis", "Técnica", "select", [
                "Trombectomía quirúrgica", "Trombectomía/tromboaspiración endovascular",
                "Trombectomía + angioplastia", "Trombectomía + revisión quirúrgica (nueva anastomosis)",
                "Otra",
            ], si=si("complicacion_acceso", "Trombosis"), req=True),
            C("tecnica_estenosis", "Técnica", "select", [
                "Angioplastia", "Angioplastia + stent", "Revisión quirúrgica (nueva anastomosis/parche)",
                "Otra",
            ], si=si("complicacion_acceso", "Estenosis/disfunción"), req=True),
            C("cirugia_asociada", "Cirugía asociada en el mismo acto", "multi", [
                "Ninguna", "Creación de un nuevo acceso", "Colocación de catéter de diálisis", "Otra",
            ], si=si("cirugia", _SECUNDARIA)),
            C("detalle_tecnica", "Detalle de la técnica / cirugía asociada", "area",
              si=si("cirugia", _SECUNDARIA)),
            C("thrill_final", "Thrill al final de la intervención", "sino"),
            *material(si=si("cirugia", _SECUNDARIA)),
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
           "Ninguna", "Infección", "Degeneración aneurismática", "Pseudoaneurisma",
           "Síndrome de robo", "Hiperaflujo/insuficiencia cardiaca", "Trombosis",
           "Estenosis venosa central",
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
            *material(),
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
              ["50-69 %", "70-99 %", "Suboclusión (near-occlusion)", "Reestenosis"], req=True, ayuda=E.AYUDA_NASCET),
            C("contralateral", "Carótida contralateral", "select", ["< 50 %", "50-69 %", "70-99 %", "Ocluida"]),
            C("rankin_preop", "Rankin modificado previo", "select", ["0", "1", "2", "3", "4", "5"], guia=E.RANKIN),
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
            *material(si=si("abordaje", "Endovascular")),
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
       C("rankin", "Rankin modificado", "select", ["0", "1", "2", "3", "4", "5", "6"], guia=E.RANKIN))],
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
            C("eva_basal", "Dolor pélvico basal (EVA 0-10)", "numero", min=0, max=10, ayuda=E.AYUDA_EVA),
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
            C("jalaie", "Clasificación de Jalaie (obstrucción venosa iliofemoral)", "select",
              [v for v, _ in E.JALAIE], guia=E.JALAIE, si=si("tecnica", "Stent venoso")),
            *material(),
        ),
        S("Clasificación SVP", *svp()),
    ],
    [S("Seguimiento específico",
       C("eva", "Dolor pélvico actual (EVA 0-10)", "numero", min=0, max=10, req=True, ayuda=E.AYUDA_EVA),
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
              ["C1", "C2", "C3", "C4a", "C4b", "C4c", "C5", "C6"], req=True, guia=E.CEAP_C),
            C("ceap_e", "CEAP - Etiología (E)", "radio", ["Primaria", "Secundaria", "Congénita"]),
            C("ceap_a", "CEAP - Anatomía (A)", "multi", ["Superficial", "Profundo", "Perforantes"]),
            C("ceap_p", "CEAP - Fisiopatología (P)", "radio", ["Reflujo", "Obstrucción", "Ambos"]),
            C("recidiva", "Varices recidivadas", "sino"),
        ),
        S("VCSS (pierna tratada)", *vcss()),
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
       C("complicaciones_venosas", "Complicaciones", "multi", [
           "Ninguna", "TVP", "EHIT/ETIT", "Tromboflebitis superficial", "Parestesias/lesión nerviosa",
           "Hiperpigmentación", "Quemadura cutánea",
       ]),
       C("ulcera", "Úlcera venosa", "select", ["No aplica", "Cicatrizada", "Abierta", "Recidivada"]),
       C("satisfaccion", "Satisfacción del paciente (0-10)", "numero", min=0, max=10)),
     S("VCSS (pierna tratada)", *vcss())],
)

# Síndrome postrombótico ------------------------------------------------------
procedimiento(
    "sindrome_postrombotico", "Síndrome postrombótico",
    "Recanalización venosa profunda (venoplastia y stent) en la obstrucción venosa postrombótica.",
    [
        S(
            "Clínica",
            C("lado", "Lado", "radio", LADO, req=True),
            C("ceap_c", "CEAP - Clínica (C)", "select",
              ["C0", "C1", "C2", "C3", "C4a", "C4b", "C4c", "C5", "C6"], req=True, guia=E.CEAP_C),
            C("meses_desde_tvp", "Tiempo desde la TVP", "numero", min=0, max=600, unidad="meses"),
            C("segmentos", "Segmentos afectados", "multi", [
                "Vena cava inferior", "Ilíaca común", "Ilíaca externa", "Femoral común",
                "Femoral/femoral profunda", "Poplítea",
            ], req=True),
            C("tipo_lesion", "Lesión", "radio", ["Oclusión", "Estenosis", "Ambas"]),
            C("jalaie", "Clasificación de Jalaie (obstrucción venosa iliofemoral)", "select",
              [v for v, _ in E.JALAIE], guia=E.JALAIE),
            C("pruebas", "Pruebas diagnósticas", "multi",
              ["Eco-doppler", "Flebo-TC", "Flebo-RM", "Flebografía", "IVUS"]),
        ),
        S(
            "Técnica",
            C("acceso", "Acceso venoso", "multi", ["Femoral", "Poplíteo", "Yugular"], req=True),
            C("tecnicas", "Técnicas", "multi", [
                "Venoplastia", "Stent venoso dedicado", "Stent no dedicado", "Trombectomía/AngioJet",
                "Endoflebectomía de femoral común (híbrido)", "FAV temporal",
            ], req=True),
            C("ivus", "IVUS intraoperatorio", "sino"),
            C("stent_infrainguinal", "Stent por debajo del ligamento inguinal", "sino"),
            *material(),
            C("anticoagulacion_post", "Tratamiento antitrombótico al alta", "multi",
              ["HBPM", "Anticoagulante oral directo", "Antagonista de la vitamina K", "Antiagregante"]),
        ),
        S("Escala de Villalta (pierna tratada)", *villalta()),
        S("VCSS (pierna tratada)", *vcss()),
        S("Clasificación SVP", *svp()),
    ],
    [S("Seguimiento específico",
       C("permeabilidad", "Permeabilidad del stent", "radio", [
           "Permeable (primaria)", "Permeable (primaria asistida)", "Permeable (secundaria)", "Ocluido",
           "No valorada",
       ], req=True),
       C("ulcera", "Úlcera venosa", "select", ["No aplica", "Cicatrizada", "Abierta", "Recidivada"]),
       C("claudicacion_venosa", "Claudicación venosa", "sino"),
       C("anticoagulacion", "Tratamiento antitrombótico actual", "multi",
         ["Ninguno", "HBPM", "Anticoagulante oral directo", "Antagonista de la vitamina K", "Antiagregante"])),
     S("Escala de Villalta (pierna tratada)", *villalta()),
     S("VCSS (pierna tratada)", *vcss())],
)

# Isquemia aguda / embolectomía ----------------------------------------------
_MMII = ["Miembro inferior derecho", "Miembro inferior izquierdo"]
procedimiento(
    "isquemia_aguda", "Isquemia aguda / embolectomía",
    "Embolectomía y trombectomía con Fogarty, tromboaspiración (AngioJet) y fibrinólisis en la "
    "isquemia aguda de extremidades.",
    [
        S(
            "Indicación",
            C("extremidad", "Extremidad", "radio",
              _MMII + ["Miembro superior derecho", "Miembro superior izquierdo"], req=True),
            C("etiologia", "Etiología", "select", [
                "Embólica", "Trombosis in situ (arteria nativa)", "Trombosis de bypass",
                "Trombosis de stent", "Aneurisma poplíteo trombosado", "Disección/traumatismo",
                "Desconocida",
            ], req=True),
            C("origen_embolia", "Origen de la embolia", "select",
              ["Fibrilación auricular", "Otra cardiopatía", "Aneurisma proximal", "Desconocido"],
              si=si("etiologia", "Embólica")),
            C("rutherford_agudo", "Clasificación de Rutherford", "select", ["I", "IIa", "IIb", "III"], req=True, guia=E.RUTHERFORD_AGUDA),
            C("horas_evolucion", "Horas de evolución", "numero", min=0, max=720, unidad="h"),
        ),
        S(
            "Técnica",
            C("abordaje", "Abordaje", "multi",
              ["Femoral", "Poplíteo", "Humeral", "Percutáneo"], req=True),
            C("embolectomia", "Embolectomía/trombectomía con catéter de Fogarty", "sino", req=True),
            C("direccion_embolectomia", "Dirección", "radio",
              ["Proximal", "Distal", "Proximal y distal"], si=si("embolectomia", "Sí"), req=True),
            C("territorios", "Territorios recanalizados", "multi", [
                "Ilíaca", "Femoral común", "Femoral superficial", "Femoral profunda", "Poplítea",
                "Troncos distales", "Subclavia/axilar", "Humeral", "Radial/cubital",
            ], si=si("embolectomia", "Sí"), req=True),
            C("tromboaspiracion", "Tromboaspiración (AngioJet)", "sino", req=True),
            C("fibrinolisis", "Fibrinólisis", "radio",
              ["No", "Intraoperatoria", "Por catéter (posoperatoria)"]),
            C("tratamiento_adjunto", "Tratamiento adjunto", "multi", [
                "Ninguno", "Angioplastia", "Stent", "Bypass", "Endarterectomía/parche", "Fasciotomía",
            ]),
            C("angiografia_final", "Angiografía de control", "sino"),
            *material(si=si("tratamiento_adjunto", "Angioplastia", "Stent")),
        ),
    ],
    [S("Seguimiento específico",
       C("permeabilidad", "Permeabilidad del eje tratado", "radio",
         ["Permeable", "Reoclusión", "No valorada"], req=True),
       C("anticoagulacion", "Anticoagulación al alta/actual", "sino"),
       *SEGUIMIENTO_EXTREMIDAD)],
)

# Traumatismo vascular -------------------------------------------------------
_abierto = ["Cirugía abierta", "Híbrido"]
_endo = ["Endovascular", "Híbrido"]
procedimiento(
    "trauma", "Traumatismo vascular",
    "Lesiones vasculares traumáticas e iatrogénicas: región, mecanismo y tratamiento abierto o endovascular.",
    [
        S(
            "Lesión",
            C("region", "Región", "radio",
              ["Miembro superior", "Miembro inferior", "Abdomen", "Tórax", "Cuello"], req=True),
            C("lado", "Lado", "radio", ["Derecho", "Izquierdo", "Línea media/no aplica"]),
            C("mecanismo", "Mecanismo", "radio", ["Penetrante", "Contuso", "Iatrogénico"], req=True),
            C("tipo_lesion", "Tipo de lesión", "multi", [
                "Sección completa", "Laceración parcial", "Disección/trombosis", "Pseudoaneurisma",
                "Fístula arteriovenosa", "Espasmo/compresión",
            ], req=True),
            C("vaso", "Vaso lesionado (opcional)"),
            C("grado_esvs", "Grado ESVS de la lesión vascular", "select",
              [v for v, _ in E.GRADO_ESVS_TRAUMA], guia=E.GRADO_ESVS_TRAUMA,
              ayuda="Si hay varias lesiones, la más grave."),
            C("lesiones_asociadas", "Lesiones asociadas", "multi", [
                "Ninguna", "Fractura/luxación", "Lesión venosa", "Lesión nerviosa", "Lesión visceral",
                "Traumatismo craneoencefálico",
            ]),
            C("shock", "Shock al ingreso", "sino"),
        ),
        S(
            "Tratamiento",
            C("tratamiento", "Tipo de tratamiento", "radio",
              ["Cirugía abierta", "Endovascular", "Híbrido", "Conservador/observación"], req=True),
            C("tecnica_abierta", "Técnica abierta", "multi", [
                "Ligadura", "Sutura/reparación directa", "Parche", "Anastomosis término-terminal",
                "Interposición de injerto venoso", "Interposición de injerto protésico", "Bypass",
                "Shunt temporal",
            ], si=si("tratamiento", *_abierto), req=True),
            C("tecnica_endo", "Técnica endovascular", "multi", [
                "Embolización", "Stent cubierto", "Stent no cubierto", "Balón de oclusión/control proximal",
            ], si=si("tratamiento", *_endo), req=True),
            *material(si=si("tratamiento", *_endo)),
            C("reparacion_venosa", "Reparación venosa asociada", "sino",
              si=si("tratamiento", *_abierto)),
            C("fasciotomia", "Fasciotomía", "sino",
              si=si("region", "Miembro superior", "Miembro inferior")),
        ),
    ],
    [S("Seguimiento específico",
       C("permeabilidad", "Permeabilidad de la reparación", "radio",
         ["Permeable", "Estenosis", "Ocluida", "No aplica (ligadura/embolización)"]),
       AMPUTACION_SEGUIMIENTO,
       C("secuelas_neurologicas", "Secuelas neurológicas en la extremidad", "sino"),
       C("infeccion", "Infección de la reparación", "sino"))],
)

# Amputaciones ---------------------------------------------------------------
_MAYORES = ["Supracondílea", "Infracondílea", "Desarticulación de rodilla", "Desarticulación de cadera"]
procedimiento(
    "amputacion", "Amputaciones",
    "Amputaciones mayores (supracondílea, infracondílea) y menores (transmetatarsiana, digital).",
    [
        S(
            "Indicación",
            C("lado", "Lado", "radio", ["Derecho", "Izquierdo"], req=True),
            C("indicacion", "Indicación", "select", [
                "Isquemia crónica (CLTI)", PIE_DIABETICO_SIN_ISQUEMIA, "Isquemia aguda", "Traumatismo",
                "Otra",
            ], req=True),
            C("pie_diabetico", "Pie diabético", "sino", si=si("indicacion", "Isquemia crónica (CLTI)")),
            C("revascularizacion_previa", "Revascularización previa de la extremidad", "radio",
              ["No", "Sí, permeable", "Sí, fracasada", "No revascularizable"]),
        ),
        S(
            "Técnica",
            C("nivel", "Nivel", "select", _MAYORES + ["Transmetatarsiana", "Chopart/Lisfranc", "Digital"],
              req=True),
            C("dedos", "Dedos amputados", "multi", ["1.º", "2.º", "3.º", "4.º", "5.º"],
              si=si("nivel", "Digital"), req=True),
            C("cierre", "Cierre", "radio", [
                "Cierre primario", "Abierta/guillotina (dos tiempos)", "Cierre diferido/terapia de presión negativa",
            ]),
            C("reamputacion", "Reamputación (nivel más proximal tras una amputación previa)", "sino"),
        ),
    ],
    [S("Seguimiento específico",
       C("estado_munon", "Estado del muñón/herida", "select",
         ["Cicatrizado", "En proceso de cicatrización", "Dehiscencia/necrosis", "Infección"], req=True),
       C("reamputacion_seguimiento", "Reamputación a un nivel superior", "radio",
         ["No", "Sí, menor", "Sí, mayor"]),
       C("deambulacion", "Deambulación", "select", [
           "Autónoma sin ayudas", "Con prótesis", "Con ayudas (bastón/andador)", "Silla de ruedas",
           "Encamado",
       ]))],
)

# Misceláneos ----------------------------------------------------------------
procedimiento(
    "miscelanea", "Misceláneos",
    "Cualquier procedimiento que no encaje en los grupos anteriores.",
    [
        S(
            "Procedimiento",
            C("categoria", "Categoría", "select", [
                "Fasciotomía", "Aneurisma periférico (no poplíteo)",
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


# Solo en el seguimiento al mes.
SEGUIMIENTO_30_DIAS = S(
    "Resultados a 30 días",
    C("reingreso_30d", "Reingreso hospitalario en los primeros 30 días", "sino", req=True),
    C("reingreso_fecha", "Fecha del reingreso", "fecha", si=si("reingreso_30d", "Sí")),
    C("reingreso_motivo", "Motivo del reingreso", "select", [
        "Infección de herida", "Trombosis/fallo del procedimiento", "Hemorragia/hematoma",
        "Isquemia de la extremidad", "Causa cardiaca", "Causa renal", "Otra",
    ], si=si("reingreso_30d", "Sí"), req=True),
    C("reingreso_relacionado", "Relacionado con el procedimiento", "sino", si=si("reingreso_30d", "Sí")),
)

# Solo cuando la intervención es una reintervención de otra registrada.
DATOS_REINTERVENCION = S(
    "Reintervención",
    C("reint_motivo", "Motivo de la reintervención", "select", [
        "Trombosis/oclusión", "Reestenosis", "Endofuga", "Migración/desconexión", "Crecimiento del saco",
        "Infección", "Complicación de la herida", "Hemorragia/hematoma", "Pseudoaneurisma",
        "Isquemia persistente/progresión de la enfermedad", "Otra",
    ], req=True),
    C("reint_relacion", "Relación con el procedimiento previo", "radio", [
        "Sobre el mismo procedimiento/lesión diana", "Misma extremidad o territorio, lesión distinta",
    ], req=True),
    C("reint_mismo_ingreso", "Durante el mismo ingreso", "sino"),
)


# ---------------------------------------------------------------------------
# Acceso a los formularios
# ---------------------------------------------------------------------------

def formulario_cirugia(tipo, reintervencion=False):
    p = PROCEDIMIENTOS[tipo]
    inicio = [DATOS_REINTERVENCION] if reintervencion else []
    return inicio + COMUN_PREOPERATORIO + p["secciones"] + [COMUN_INTRAOPERATORIO] + COMUN_POSTOPERATORIO


def formulario_seguimiento(tipo, hito=None):
    """Con hito=None devuelve todos los campos posibles (útil para exportar)."""
    treinta = [SEGUIMIENTO_30_DIAS] if hito in (None, "1m") else []
    return COMUN_SEGUIMIENTO + treinta + PROCEDIMIENTOS[tipo]["seguimiento"]


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
        if tipo == "calculado":
            valor = calcular(c, datos)
            if valor:
                datos[nombre] = valor
            continue
        if tipo == "dispositivos":
            valor, error = _procesar_dispositivos(nombre, form)
            if error:
                errores[nombre] = error
                continue
        elif tipo == "multi":
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


def _clave(valor):
    return str(valor).split(" ")[0] if valor not in (None, "", []) else ""


def calcular(campo, datos):
    """Valor de un campo calculado (o None si faltan datos). Misma lógica en formulario.js."""
    regla = campo["calculado"]
    if "suma" in regla:
        claves = [_clave(datos.get(n)) for n in regla["suma"]]
        return sum(int(k) for k in claves) if all(k.isdigit() for k in claves) else None
    if "svp" in regla:
        return codigo_svp(datos)
    claves = [_clave(datos.get(n)) for n in regla["entradas"]]
    if not all(claves):
        return None
    if "rangos" in regla:
        forzar = regla.get("forzar")
        if forzar and datos.get(forzar["campo"]) == forzar["valor"]:
            return forzar["texto"]
        total = float(claves[0])
        return next((texto for hasta, texto in regla["rangos"] if total <= hasta), None)
    return regla["tabla"].get("|".join(claves))


def codigo_svp(datos):
    """«S2,3a V2 P LGV,R,NT; LIIV,R,NT» a partir de los campos svp_*."""
    s, v, segmentos = datos.get("svp_s") or [], datos.get("svp_v") or [], datos.get("svp_anatomia") or []
    etiologia = datos.get("svp_etiologia")
    if not s or not v:
        return None
    codigo = "S" + ",".join(x[1:] for x in s) + " V" + ",".join(x[1:] for x in v)
    if segmentos and etiologia and all(datos.get(f"svp_h_{seg}") for seg in segmentos):
        codigo += " P " + "; ".join(f"{seg},{datos[f'svp_h_{seg}']},{etiologia}" for seg in segmentos)
    return codigo


COLUMNAS_DISPOSITIVO = ("tipo", "vaso", "modelo", "diametro", "longitud")


def _procesar_dispositivos(nombre, form):
    columnas = {col: form.getlist(f"{nombre}__{col}") for col in COLUMNAS_DISPOSITIVO}
    filas = []
    for i in range(max(len(v) for v in columnas.values())):
        fila = {col: (columnas[col][i] if i < len(columnas[col]) else "").strip() for col in COLUMNAS_DISPOSITIVO}
        if not any(fila.values()):
            continue
        if fila["tipo"] not in TIPOS_DISPOSITIVO:
            return None, f"Fila {len(filas) + 1}: elige el tipo de dispositivo."
        for col, maximo in (("diametro", 60), ("longitud", 500)):
            if fila[col]:
                try:
                    numero = float(fila[col].replace(",", "."))
                except ValueError:
                    return None, f"Fila {len(filas) + 1}: el {col} debe ser un número."
                if not 0 < numero <= maximo:
                    return None, f"Fila {len(filas) + 1}: {col} fuera de rango (0-{maximo} mm)."
                fila[col] = int(numero) if numero.is_integer() else numero
        filas.append({k: v for k, v in fila.items() if v != ""})
    return filas, None


def _fecha_valida(texto):
    from datetime import date
    try:
        date.fromisoformat(texto)
        return True
    except ValueError:
        return False


def dispositivo_legible(d):
    medidas = "×".join(str(d[k]) for k in ("diametro", "longitud") if k in d)
    partes = [d.get("tipo", ""), f"{medidas} mm" if medidas else "",
              f"({d['modelo']})" if d.get("modelo") else "", f"en {d['vaso']}" if d.get("vaso") else ""]
    return " ".join(p for p in partes if p)


def valor_legible(valor, campo=None):
    """Texto de un valor guardado; si el campo es una escala, añade la descripción de la opción."""
    desc = (campo or {}).get("descripciones", {})

    def texto(v):
        if isinstance(v, dict):
            return dispositivo_legible(v)
        return f"{v} · {desc[v]}" if v in desc else str(v)
    if isinstance(valor, list):
        return " | ".join(texto(v) for v in valor)
    return "" if valor is None else texto(valor)
