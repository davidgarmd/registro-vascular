"""Guías breves de las escalas y clasificaciones usadas en los formularios.

Cada guía es una lista de pares (valor, descripción) que se muestra bajo el campo
como «¿Cómo se clasifica?». Son resúmenes orientativos: ante la duda, consultad la
publicación original de cada escala.
"""

ASA = [
    ("I", "Paciente sano."),
    ("II", "Enfermedad sistémica leve, sin limitación funcional (p. ej., HTA o diabetes bien controladas, fumador)."),
    ("III", "Enfermedad sistémica grave con limitación funcional (p. ej., diabetes mal controlada, EPOC, "
            "obesidad mórbida, cardiopatía isquémica estable, diálisis)."),
    ("IV", "Enfermedad sistémica grave que es una amenaza constante para la vida (p. ej., IAM o ictus "
           "recientes, isquemia coronaria activa, disfunción valvular o ventricular grave, sepsis)."),
    ("V", "Paciente moribundo que no se espera que sobreviva sin la operación (p. ej., aneurisma roto)."),
]

CLAVIEN_DINDO = [
    ("0", "Sin complicaciones."),
    ("I", "Cualquier desviación del postoperatorio normal que no requiere tratamiento farmacológico, "
          "quirúrgico, endoscópico ni radiológico. Se permiten antieméticos, antipiréticos, analgésicos, "
          "diuréticos, electrolitos, fisioterapia y abrir una herida infectada a pie de cama."),
    ("II", "Requiere tratamiento farmacológico distinto de los anteriores (p. ej., antibióticos). "
           "Incluye transfusión y nutrición parenteral."),
    ("IIIa", "Requiere intervención quirúrgica, endoscópica o radiológica SIN anestesia general."),
    ("IIIb", "Requiere intervención quirúrgica, endoscópica o radiológica CON anestesia general "
             "(p. ej., revisión de hematoma o trombectomía en quirófano)."),
    ("IVa", "Complicación con riesgo vital que requiere UCI: fallo de un órgano (incluida la diálisis)."),
    ("IVb", "Complicación con riesgo vital que requiere UCI: fallo multiorgánico."),
    ("V", "Muerte del paciente."),
]

WIFI_W = [
    ("0", "Sin úlcera ni gangrena (dolor isquémico en reposo)."),
    ("1", "Úlcera pequeña y superficial en pierna o pie distal, sin hueso expuesto (salvo falange distal)."),
    ("2", "Úlcera más profunda con hueso, articulación o tendón expuestos, o gangrena limitada a dedos."),
    ("3", "Úlcera extensa y profunda del antepié y/o mediopié, úlcera profunda del talón, o gangrena "
          "extensa de antepié, mediopié o talón."),
]
WIFI_I = [
    ("0", "ITB ≥ 0,80 · presión en tobillo > 100 mmHg · presión en dedo o TcPO₂ ≥ 60 mmHg."),
    ("1", "ITB 0,60-0,79 · tobillo 70-100 mmHg · dedo/TcPO₂ 40-59 mmHg."),
    ("2", "ITB 0,40-0,59 · tobillo 50-70 mmHg · dedo/TcPO₂ 30-39 mmHg."),
    ("3", "ITB ≤ 0,39 · tobillo < 50 mmHg · dedo/TcPO₂ < 30 mmHg."),
]
WIFI_FI = [
    ("0", "Sin signos ni síntomas de infección."),
    ("1", "Infección local de piel y subcutáneo; eritema de 0,5 a 2 cm alrededor de la úlcera."),
    ("2", "Infección local con eritema > 2 cm o que afecta a estructuras profundas (absceso, "
          "osteomielitis, artritis séptica, fascitis), sin respuesta inflamatoria sistémica."),
    ("3", "Infección local con signos de respuesta inflamatoria sistémica (SIRS)."),
]

RUTHERFORD_AGUDA = [
    ("I · Viable", "Sin amenaza inmediata. Sin pérdida sensitiva ni debilidad. Doppler arterial audible."),
    ("IIa · Amenaza marginal", "Salvable con tratamiento rápido. Pérdida sensitiva mínima (dedos) o nula; "
                               "sin debilidad. Doppler arterial a menudo inaudible, venoso audible."),
    ("IIb · Amenaza inmediata", "Salvable con revascularización inmediata. Pérdida sensitiva más allá de los "
                                "dedos, dolor en reposo y debilidad leve-moderada. Arterial inaudible, venoso audible."),
    ("III · Irreversible", "Pérdida de tejido o lesión nerviosa permanente inevitable. Anestesia profunda, "
                           "parálisis (rigidez). Doppler arterial y venoso inaudibles."),
]

TASC_AORTOILIACO = [
    ("A", "Estenosis uni o bilateral de ilíaca común. Estenosis única y corta (≤ 3 cm) de ilíaca externa."),
    ("B", "Estenosis corta (≤ 3 cm) de aorta infrarrenal. Oclusión unilateral de ilíaca común. Estenosis de "
          "3-10 cm de ilíaca externa sin llegar a femoral común. Oclusión unilateral de ilíaca externa que no "
          "afecta al origen de hipogástrica ni a femoral común."),
    ("C", "Oclusión bilateral de ilíacas comunes. Estenosis bilateral de 3-10 cm de ilíaca externa. Estenosis "
          "de ilíaca externa que se extiende a femoral común. Oclusión de ilíaca externa que afecta al origen "
          "de hipogástrica y/o femoral común, o muy calcificada."),
    ("D", "Oclusión aortoilíaca infrarrenal. Enfermedad difusa de aorta y ambas ilíacas. Estenosis múltiples "
          "difusas de ilíaca común, externa y femoral común. Oclusión de ilíaca común y externa del mismo lado. "
          "Oclusión bilateral de ilíacas externas. Estenosis ilíacas con aneurisma de aorta que requiere cirugía."),
]
TASC_FEMOROPOPLITEO = [
    ("A", "Estenosis única ≤ 10 cm. Oclusión única ≤ 5 cm."),
    ("B", "Lesiones múltiples (estenosis u oclusiones) de ≤ 5 cm cada una. Estenosis u oclusión única ≤ 15 cm "
          "que no afecta a la poplítea infragenicular. Oclusión muy calcificada ≤ 5 cm. Estenosis poplítea única."),
    ("C", "Estenosis u oclusiones múltiples que suman > 15 cm. Reestenosis u oclusión recurrente tras dos "
          "tratamientos endovasculares."),
    ("D", "Oclusión crónica de femoral común o superficial > 20 cm que afecta a la poplítea. Oclusión crónica "
          "de la poplítea y del origen de los troncos distales."),
]

PACSS = [
    ("0", "Sin calcificación visible en la lesión diana."),
    ("1", "Calcificación en una sola pared, < 5 cm de longitud."),
    ("2", "Calcificación en una sola pared, ≥ 5 cm."),
    ("3", "Calcificación en ambas paredes (circunferencial), < 5 cm."),
    ("4", "Calcificación en ambas paredes (circunferencial), ≥ 5 cm."),
]

# GLASS (Global Limb Anatomic Staging System, Global Vascular Guidelines 2019).
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
GUIA_GLASS = [
    ("Antes de puntuar", "Elige la vía arterial diana: el eje que se va a revascularizar desde la ingle hasta "
                         "el pie. Puntúa solo esa vía."),
    ("Calcificación", "La calcificación grave (> 50 % de la circunferencia, difusa, voluminosa o «en coral») "
                      "sube un grado el segmento afectado."),
    ("Entrada", "La enfermedad aortoilíaca se registra aparte; no modifica el estadio."),
    ("Estadio I", "Fallo técnico esperado < 10 %; permeabilidad de la extremidad al año > 70 %."),
    ("Estadio II", "Fallo técnico esperado < 20 %; permeabilidad al año 50-70 %."),
    ("Estadio III", "Fallo técnico esperado > 20 %; permeabilidad al año < 50 %. Favorece el bypass si hay vena."),
]

CRAWFORD = [
    ("I", "Desde la subclavia izquierda hasta por encima de las arterias renales."),
    ("II", "Desde la subclavia izquierda hasta por debajo de las renales (puede llegar a la bifurcación)."),
    ("III", "Desde la mitad de la aorta torácica descendente (~T6) hasta por debajo de las renales."),
    ("IV", "Desde el diafragma (~T12) hasta la bifurcación: toda la aorta abdominal."),
    ("V", "Desde ~T6 hasta por encima de las renales (Safi)."),
]

ISHIMARU = [
    ("0", "Aorta ascendente, hasta el origen del tronco braquiocefálico incluido."),
    ("1", "Entre el tronco braquiocefálico y la carótida común izquierda."),
    ("2", "Entre la carótida común izquierda y la subclavia izquierda."),
    ("3", "Primeros 2 cm distales a la subclavia izquierda."),
    ("4", "Resto de la aorta torácica descendente."),
]

ENDOFUGAS = [
    ("Tipo Ia", "Fallo de sellado en el anclaje proximal."),
    ("Tipo Ib", "Fallo de sellado en el anclaje distal (ilíaco)."),
    ("Tipo II", "Relleno retrógrado del saco por ramas (lumbares, mesentérica inferior, hipogástrica)."),
    ("Tipo III", "Desconexión entre módulos o rotura del tejido de la endoprótesis."),
    ("Tipo IV", "Porosidad del tejido (en los primeros 30 días, con anticoagulación)."),
    ("Endotensión (tipo V)", "Crecimiento del saco sin endofuga visible."),
]

RANKIN = [
    ("0", "Sin síntomas."),
    ("1", "Sin discapacidad significativa: puede hacer sus actividades habituales pese a algún síntoma."),
    ("2", "Discapacidad leve: no puede hacer todo lo que hacía, pero es autónomo."),
    ("3", "Discapacidad moderada: necesita alguna ayuda, pero camina sin ayuda."),
    ("4", "Discapacidad moderadamente grave: no camina sin ayuda y necesita ayuda para su cuidado."),
    ("5", "Discapacidad grave: encamado, incontinente, requiere cuidados constantes."),
    ("6", "Muerte."),
]

CEAP_C = [
    ("C0", "Sin signos visibles ni palpables de enfermedad venosa."),
    ("C1", "Telangiectasias o venas reticulares."),
    ("C2", "Varices (≥ 3 mm de diámetro en bipedestación)."),
    ("C3", "Edema."),
    ("C4a", "Pigmentación o eccema."),
    ("C4b", "Lipodermatoesclerosis o atrofia blanca."),
    ("C4c", "Corona flebectásica."),
    ("C5", "Úlcera venosa cicatrizada."),
    ("C6", "Úlcera venosa activa."),
]

VCSS = [
    ("Qué puntúa", "10 elementos, de 0 (ausente) a 3 (grave) cada uno: dolor, varices, edema, pigmentación, "
                   "inflamación, induración, número de úlceras activas, duración de la úlcera, tamaño de la "
                   "úlcera y uso de compresión."),
    ("Total", "De 0 a 30. Cuanto más alto, más grave."),
]

VILLALTA = [
    ("Qué puntúa", "5 síntomas (dolor, calambres, pesadez, parestesias, prurito) y 6 signos (edema, induración "
                   "de la piel, hiperpigmentación, enrojecimiento, ectasia venosa y dolor a la compresión de la "
                   "pantorrilla), de 0 (ausente) a 3 (grave) cada uno."),
    ("Interpretación", "0-4: sin síndrome postrombótico · 5-9: leve · 10-14: moderado · ≥ 15 o úlcera "
                       "venosa: grave."),
]

NASCET = [
    ("Cálculo", "Estenosis (%) = (1 - diámetro residual mínimo / diámetro de la carótida interna distal "
                "normal) × 100."),
    ("Por eco-doppler", "Orientativo: 50-69 % con VPS 125-230 cm/s; ≥ 70 % con VPS > 230 cm/s o índice "
                        "ACI/ACC > 4."),
]

EVA = [
    ("Escala", "0 = sin dolor; 10 = el peor dolor imaginable. Pregunta por el dolor habitual de la última semana."),
]

DISECCION_TIPO_B = [
    ("Complicada", "Rotura o malperfusión (visceral, renal, medular o de extremidades)."),
    ("De alto riesgo", "Sin rotura ni malperfusión, pero con rasgos de mal pronóstico: dolor o hipertensión "
                       "refractarios, diámetro aórtico ≥ 40 mm, falsa luz amplia, puerta de entrada grande o "
                       "derrame pleural hemático, entre otros."),
    ("No complicada", "Ninguno de los anteriores."),
]
