"""Escalas y clasificaciones usadas en los formularios.

Cada escala es una lista de pares (valor, descripción breve). La descripción se
muestra junto a cada opción del desplegable («IIIb · Requiere intervención…»),
pero lo que se guarda es solo el valor. Son resúmenes orientativos: ante la duda,
consultad la publicación original de cada escala.

Las escalas compuestas (WIfI, GLASS, Villalta, VCSS, SVP) no se eligen: se
calculan a partir de sus componentes (ver `formularios.calcular`).
"""

ASA = [
    ("I", "Paciente sano"),
    ("II", "Enfermedad sistémica leve, sin limitación funcional"),
    ("III", "Enfermedad sistémica grave, con limitación funcional"),
    ("IV", "Enfermedad sistémica grave, amenaza constante para la vida"),
    ("V", "Moribundo, no sobrevivirá sin la operación"),
]

CLAVIEN_DINDO = [
    ("I", "Desviación del curso normal sin tratamiento específico (analgesia, antieméticos…)"),
    ("II", "Requiere fármacos (p. ej., antibióticos), transfusión o nutrición parenteral"),
    ("IIIa", "Intervención quirúrgica/endoscópica/radiológica SIN anestesia general"),
    ("IIIb", "Intervención quirúrgica/endoscópica/radiológica CON anestesia general"),
    ("IVa", "UCI por fallo de un órgano (incluida diálisis)"),
    ("IVb", "UCI por fallo multiorgánico"),
    ("V", "Muerte del paciente"),
]

# WIfI (SVS, Mills 2014) ---------------------------------------------------------
WIFI_W = [
    ("0", "Sin úlcera ni gangrena (dolor en reposo)"),
    ("1", "Úlcera pequeña y superficial, sin hueso expuesto (salvo falange distal)"),
    ("2", "Úlcera profunda con hueso/tendón expuesto, o gangrena limitada a dedos"),
    ("3", "Úlcera extensa de antepié/mediopié o talón profunda, o gangrena extensa"),
]
WIFI_I = [
    ("0", "ITB ≥ 0,80 · tobillo > 100 mmHg · dedo/TcPO₂ ≥ 60 mmHg"),
    ("1", "ITB 0,60-0,79 · tobillo 70-100 · dedo/TcPO₂ 40-59 mmHg"),
    ("2", "ITB 0,40-0,59 · tobillo 50-70 · dedo/TcPO₂ 30-39 mmHg"),
    ("3", "ITB ≤ 0,39 · tobillo < 50 · dedo/TcPO₂ < 30 mmHg"),
]
WIFI_FI = [
    ("0", "Sin infección"),
    ("1", "Local, piel y subcutáneo, eritema 0,5-2 cm"),
    ("2", "Local, eritema > 2 cm o estructuras profundas (absceso, osteomielitis), sin SIRS"),
    ("3", "Infección con respuesta inflamatoria sistémica (SIRS)"),
]
# Riesgo de amputación al año → estadio clínico. Filas: W 0-3; dentro de cada fila,
# un bloque por grado de isquemia (I 0-3) con los cuatro grados de infección (fI 0-3).
_MATRIZ_WIFI = [
    ["1123", "1234", "2234", "2334"],   # W0
    ["1124", "2344", "3344", "3444"],   # W1
    ["2234", "3344", "3444", "4444"],   # W2
    ["3344", "4444", "4444", "4444"],   # W3
]
WIFI_ESTADIOS = {
    "1": "Estadio 1 (riesgo de amputación muy bajo)",
    "2": "Estadio 2 (riesgo bajo)",
    "3": "Estadio 3 (riesgo moderado)",
    "4": "Estadio 4 (riesgo alto)",
}
TABLA_WIFI = {
    f"{w}|{i}|{fi}": WIFI_ESTADIOS[_MATRIZ_WIFI[w][i][fi]]
    for w in range(4) for i in range(4) for fi in range(4)
}

RUTHERFORD_AGUDA = [
    ("I", "Viable: sin pérdida sensitiva ni motora; doppler arterial audible"),
    ("IIa", "Amenaza marginal: hipoestesia mínima (dedos), sin debilidad"),
    ("IIb", "Amenaza inmediata: hipoestesia más allá de los dedos, dolor en reposo, debilidad leve-moderada"),
    ("III", "Irreversible: anestesia y parálisis; doppler arterial y venoso inaudibles"),
]

TASC_AORTOILIACO = [
    ("A", "Estenosis de ilíaca común (uni o bilateral) o de ilíaca externa corta (≤ 3 cm)"),
    ("B", "Estenosis aórtica corta, oclusión unilateral de ilíaca común o externa sin afectar a femoral"),
    ("C", "Oclusión bilateral de ilíacas comunes, o ilíaca externa hasta femoral común"),
    ("D", "Oclusión aortoilíaca infrarrenal o enfermedad difusa aorta + ambas ilíacas"),
]
TASC_FEMOROPOPLITEO = [
    ("A", "Estenosis única ≤ 10 cm u oclusión única ≤ 5 cm"),
    ("B", "Lesiones múltiples ≤ 5 cm, o única ≤ 15 cm sin poplítea infragenicular"),
    ("C", "Lesiones múltiples que suman > 15 cm, o reestenosis tras 2 tratamientos"),
    ("D", "Oclusión de femoral común/superficial > 20 cm, o de poplítea y trifurcación"),
]

PACSS = [
    ("0", "Sin calcificación"),
    ("1", "Una pared, < 5 cm"),
    ("2", "Una pared, ≥ 5 cm"),
    ("3", "Ambas paredes, < 5 cm"),
    ("4", "Ambas paredes, ≥ 5 cm"),
]

# GLASS (Global Vascular Guidelines 2019) -----------------------------------------
GLASS_FP = [
    "0 · Sin enfermedad significativa (< 50 %)",
    "1 · AFS < 1/3 (< 10 cm); oclusión focal < 5 cm; poplítea sin lesiones",
    "2 · AFS 1/3-2/3 (10-20 cm); oclusión < 10 cm; estenosis poplítea focal < 2 cm",
    "3 · AFS > 2/3 (> 20 cm); oclusión ostial < 20 cm u oclusión de 10-20 cm; estenosis poplítea 2-5 cm",
    "4 · Oclusión de AFS > 20 cm; poplítea > 5 cm, hasta la trifurcación u ocluida",
]
GLASS_IP = [
    "0 · Sin enfermedad significativa (< 50 %) en la arteria diana",
    "1 · Estenosis tibial focal < 3 cm (sin tronco tibioperoneo)",
    "2 · Estenosis en 1/3 del vaso; oclusión focal < 3 cm",
    "3 · Enfermedad hasta 2/3 del vaso; oclusión hasta 1/3 (puede incluir el origen)",
    "4 · Enfermedad > 2/3 del vaso; oclusión > 1/3; oclusión del tronco tibioperoneo",
]
GLASS_IM = [
    "P0 · La arteria diana cruza el tobillo y el arco plantar está íntegro",
    "P1 · La arteria diana cruza el tobillo; arco plantar ausente o muy enfermo",
    "P2 · Ninguna arteria diana cruza el tobillo hasta el pie",
]
GLASS_NA = "No aplicable (sin enfermedad significativa)"
GLASS_ESTADIOS = {
    "I": "Estadio I (baja complejidad)",
    "II": "Estadio II (complejidad intermedia)",
    "III": "Estadio III (alta complejidad)",
}
# Matriz oficial: fila = grado femoropoplíteo, columna = grado infrapoplíteo.
_MATRIZ_GLASS = [
    ["NA", "I", "I", "II", "III"],
    ["I", "I", "II", "II", "III"],
    ["I", "II", "II", "III", "III"],
    ["II", "II", "III", "III", "III"],
    ["III", "III", "III", "III", "III"],
]
TABLA_GLASS = {
    f"{fp}|{ip}": GLASS_ESTADIOS.get(estadio, GLASS_NA)
    for fp, fila in enumerate(_MATRIZ_GLASS) for ip, estadio in enumerate(fila)
}
AYUDA_GLASS = ("Puntúa solo la vía arterial diana (de la ingle al pie). La calcificación grave sube un "
               "grado el segmento afectado.")

# Aorta ---------------------------------------------------------------------------
CRAWFORD = [
    ("I", "Subclavia izquierda → por encima de las renales"),
    ("II", "Subclavia izquierda → por debajo de las renales"),
    ("III", "Mitad de la torácica descendente (T6) → por debajo de las renales"),
    ("IV", "Diafragma (T12) → bifurcación: toda la aorta abdominal"),
    ("V", "T6 → por encima de las renales (Safi)"),
]

ISHIMARU = [
    ("0", "Aorta ascendente hasta el tronco braquiocefálico incluido"),
    ("1", "Entre tronco braquiocefálico y carótida común izquierda"),
    ("2", "Entre carótida común izquierda y subclavia izquierda"),
    ("3", "Primeros 2 cm distales a la subclavia izquierda"),
    ("4", "Resto de la aorta torácica descendente"),
]

ENDOFUGAS = [
    ("Tipo Ia", "Fallo de sellado proximal"),
    ("Tipo Ib", "Fallo de sellado distal"),
    ("Tipo II", "Relleno retrógrado por ramas (lumbares, AMI, hipogástrica)"),
    ("Tipo III", "Desconexión de módulos o rotura del tejido"),
    ("Tipo IV", "Porosidad del tejido"),
    ("Endotensión (tipo V)", "Crecimiento del saco sin endofuga visible"),
]

DISECCION_TIPO_B = [
    ("Complicada", "Rotura o malperfusión"),
    ("De alto riesgo", "Dolor/HTA refractarios, aorta ≥ 40 mm, falsa luz amplia, derrame hemático…"),
    ("No complicada", "Ninguno de los anteriores"),
]

# Carótida ------------------------------------------------------------------------
RANKIN = [
    ("0", "Sin síntomas"),
    ("1", "Sin discapacidad significativa"),
    ("2", "Discapacidad leve, autónomo"),
    ("3", "Discapacidad moderada, camina sin ayuda"),
    ("4", "Moderadamente grave, no camina sin ayuda"),
    ("5", "Grave: encamado, cuidados constantes"),
    ("6", "Muerte"),
]
AYUDA_NASCET = "NASCET = (1 − diámetro residual / ACI distal normal) × 100. Eco: ≥ 70 % si VPS > 230 cm/s."

# Venoso --------------------------------------------------------------------------
CEAP_C = [
    ("C0", "Sin signos visibles ni palpables"),
    ("C1", "Telangiectasias o venas reticulares"),
    ("C2", "Varices (≥ 3 mm)"),
    ("C3", "Edema"),
    ("C4a", "Pigmentación o eccema"),
    ("C4b", "Lipodermatoesclerosis o atrofia blanca"),
    ("C4c", "Corona flebectásica"),
    ("C5", "Úlcera cicatrizada"),
    ("C6", "Úlcera activa"),
]
AYUDA_EVA = "0 = sin dolor; 10 = el peor dolor imaginable (dolor habitual de la última semana)."

# Villalta: 5 síntomas y 6 signos, 0-3 cada uno, + úlcera venosa.
_INTENSIDAD = [("0", "Ausente"), ("1", "Leve"), ("2", "Moderado"), ("3", "Grave")]
VILLALTA_ITEMS = [
    ("dolor", "Dolor"), ("calambres", "Calambres"), ("pesadez", "Pesadez"),
    ("parestesias", "Parestesias"), ("prurito", "Prurito"),
    ("edema", "Edema pretibial"), ("induracion", "Induración cutánea"),
    ("hiperpigmentacion", "Hiperpigmentación"), ("enrojecimiento", "Enrojecimiento"),
    ("ectasia", "Ectasia venosa"), ("dolor_compresion", "Dolor a la compresión de la pantorrilla"),
]
VILLALTA_INTENSIDAD = _INTENSIDAD
VILLALTA_GRADOS = [(4, "Sin síndrome postrombótico"), (9, "Leve"), (14, "Moderado"), (33, "Grave")]
VILLALTA_GRAVE_POR_ULCERA = "Grave (úlcera venosa)"

# VCSS revisado (Vasquez 2010): 10 elementos, 0-3 cada uno.
_DISTRIBUCION = [("0", "Ninguna o focal"), ("1", "Limitada a la región perimaleolar"),
                 ("2", "Difusa en el tercio inferior de la pierna"),
                 ("3", "Más extensa, por encima del tercio inferior")]
VCSS_ITEMS = [
    ("dolor", "Dolor", [
        ("0", "Ninguno"), ("1", "Ocasional, no limita ni requiere analgesia"),
        ("2", "Diario, limita algo, analgesia ocasional"), ("3", "Diario, limita mucho o analgesia habitual")]),
    ("varices", "Varices (≥ 3 mm)", [
        ("0", "Ninguna"), ("1", "Pocas y dispersas (incluye corona flebectásica)"),
        ("2", "Limitadas a pantorrilla o muslo"), ("3", "En pantorrilla y muslo")]),
    ("edema", "Edema venoso", [
        ("0", "Ninguno"), ("1", "Pie y tobillo"), ("2", "Por encima del tobillo, bajo la rodilla"),
        ("3", "Hasta la rodilla o por encima")]),
    ("pigmentacion", "Pigmentación", _DISTRIBUCION),
    ("inflamacion", "Inflamación (eritema, celulitis, eccema)", _DISTRIBUCION),
    ("induracion", "Induración (lipodermatoesclerosis, atrofia blanca)", _DISTRIBUCION),
    ("n_ulceras", "Úlceras activas (número)", [("0", "Ninguna"), ("1", "1"), ("2", "2"), ("3", "3 o más")]),
    ("duracion_ulcera", "Duración de la úlcera activa", [
        ("0", "Sin úlcera"), ("1", "< 3 meses"), ("2", "3-12 meses"), ("3", "> 1 año sin cicatrizar")]),
    ("tamano_ulcera", "Tamaño de la úlcera activa", [
        ("0", "Sin úlcera"), ("1", "< 2 cm"), ("2", "2-6 cm"), ("3", "> 6 cm")]),
    ("compresion", "Terapia compresiva", [
        ("0", "No usa"), ("1", "Uso intermitente"), ("2", "La mayoría de los días"),
        ("3", "Diaria + elevación de piernas")]),
]

# SVP de los trastornos venosos pélvicos (Meissner, JVS-VL 2021).
SVP_S = [
    ("S0", "Sin síntomas renales, pélvicos ni extrapélvicos de origen venoso"),
    ("S1", "Síntomas renales de origen venoso (hematuria, dolor en flanco)"),
    ("S2", "Dolor pélvico crónico de origen venoso"),
    ("S3a", "Síntomas en venas de genitales externos"),
    ("S3b", "Síntomas en venas no safenas de la pierna de origen pélvico"),
    ("S3c", "Claudicación venosa"),
]
SVP_V = [
    ("V0", "Sin varices abdominales, pélvicas ni extrapélvicas de origen pélvico"),
    ("V1", "Varices del hilio renal"),
    ("V2", "Varices pélvicas"),
    ("V3a", "Varices genitales (vulvares, varicocele)"),
    ("V3b", "Varices de la pierna de origen pélvico"),
]
SVP_ANATOMIA = [
    ("IVC", "Vena cava inferior"),
    ("LRV", "Vena renal izquierda"),
    ("LGV", "Vena gonadal izquierda"), ("RGV", "Vena gonadal derecha"),
    ("LCIV", "Ilíaca común izquierda"), ("RCIV", "Ilíaca común derecha"),
    ("LEIV", "Ilíaca externa izquierda"), ("REIV", "Ilíaca externa derecha"),
    ("LIIV", "Ilíaca interna izquierda"), ("RIIV", "Ilíaca interna derecha"),
    ("PELV", "Puntos de fuga pélvicos"),
]
SVP_HEMODINAMICA = [("R", "Reflujo"), ("O", "Obstrucción"), ("R,O", "Reflujo y obstrucción")]
SVP_ETIOLOGIA = [("T", "Trombótica"), ("NT", "No trombótica"), ("C", "Congénita")]

# Jalaie: obstrucción venosa crónica iliofemoral (Aachen, EJVES 2023).
JALAIE = [
    ("1", "Lesión ilíaca no trombótica (NIVL, May-Thurner)"),
    ("2", "Obstrucción postrombótica limitada al segmento ilíaco"),
    ("3", "Iliofemoral, por encima de la confluencia de la femoral común"),
    ("4a", "Iliofemoral que afecta a la vena femoral"),
    ("4b", "Iliofemoral que afecta a la femoral profunda"),
    ("5", "Iliofemoral que afecta a ambas venas de entrada (femoral y femoral profunda)"),
]

# Traumatismo: gradación de la lesión vascular (guía ESVS 2025 de trauma vascular).
GRADO_ESVS_TRAUMA = [
    ("1", "Lesión de íntima o pared (flap, hematoma intramural) con contorno externo normal"),
    ("2", "Contorno externo anormal o rotura contenida (p. ej., pseudoaneurisma)"),
    ("3", "Sección completa de la pared con sangrado activo libre"),
    ("X", "Oclusión del vaso con isquemia distal"),
]
