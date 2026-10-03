"""Actividad mensual: asigna cada intervención a una patología y la agrupa por meses.

La recogida se hace por procedimiento; la patología se deduce de la indicación
registrada. Las reglas están en `clasificar` y se pueden ajustar sin tocar los datos:
el informe se recalcula cada vez.

- Las amputaciones cuentan en la patología que las causó, y además aparecen como
  procedimiento propio en la tabla por tipo de procedimiento.
- El pie diabético con isquemia cuenta como isquemia crónica (con la marca «pie
  diabético»); solo el pie diabético sin isquemia tiene categoría propia.
- Las reintervenciones cuentan como intervenciones normales y además se dan aparte.
"""
from collections import defaultdict

from .db import cargar_json, get_db
from .formularios import PIE_DIABETICO_SIN_ISQUEMIA, PROCEDIMIENTOS

AAA = "Aneurisma de aorta abdominal e ilíaco"
TORACICA = "Aorta torácica y toracoabdominal"
OCLUSIVA = "Enfermedad oclusiva aortoilíaca"
CRONICA = "Isquemia crónica de miembros inferiores"
AGUDA = "Isquemia aguda"
PERIFERICOS = "Aneurismas periféricos"
CAROTIDA = "Enfermedad carotídea"
VISCERAL = "Patología visceral"
ACCESO = "Acceso vascular para hemodiálisis"
VARICES = "Varices"
PELVICA = "Congestión venosa pélvica"
POSTROMBOTICO = "Síndrome postrombótico"
TRAUMA = "Traumatismo vascular"
INFECCION = "Infección protésica/aórtica"
PIE_DIABETICO = "Pie diabético sin isquemia"
OTROS = "Otros"

PATOLOGIAS = [AAA, TORACICA, OCLUSIVA, CRONICA, AGUDA, PERIFERICOS, CAROTIDA, VISCERAL, ACCESO,
              VARICES, PELVICA, POSTROMBOTICO, TRAUMA, INFECCION, PIE_DIABETICO, OTROS]

CLAUDICANTE = "Claudicante"
NO_CLAUDICANTE = "No claudicante (isquemia crónica amenazante)"
_INDICACION_PERIFERICA = {
    "Claudicación intermitente": (CRONICA, CLAUDICANTE),
    "Isquemia crónica: dolor en reposo": (CRONICA, NO_CLAUDICANTE),
    "Isquemia crónica: lesión trófica": (CRONICA, NO_CLAUDICANTE),
    "Rescate de bypass/stent previo": (CRONICA, "Rescate de revascularización previa"),
    "Isquemia aguda": (AGUDA, ""),
    "Aneurisma poplíteo": (PERIFERICOS, "Aneurisma poplíteo"),
    "Traumatismo": (TRAUMA, ""),
}


def clasificar(tipo, datos):
    """Devuelve (patología, subgrupo) de una intervención."""
    ind = datos.get("indicacion", "")
    if tipo == "aorta_abierta":
        if ind == "Aneurisma toracoabdominal":
            return TORACICA, "Cirugía abierta"
        if ind == "Enfermedad oclusiva aortoilíaca":
            return OCLUSIVA, ""
        if ind in ("Infección de prótesis/aortitis", "Fístula aortoentérica"):
            return INFECCION, ind
        if ind == "Otra":
            return OTROS, "Aorta abierta"
        return AAA, "Cirugía abierta"
    if tipo == "evar":
        if ind == "Aneurisma toracoabdominal":
            return TORACICA, datos.get("variante", "")
        if ind == "Otra":
            return OTROS, "EVAR"
        return AAA, datos.get("variante", "")
    if tipo == "tevar":
        return TORACICA, datos.get("patologia", "")
    if tipo in ("bypass", "endo_periferico"):
        return _INDICACION_PERIFERICA.get(ind, (OTROS, ind))
    if tipo == "isquemia_aguda":
        return AGUDA, datos.get("etiologia", "")
    if tipo == "carotida":
        sint = datos.get("sintomatologia", "")
        return CAROTIDA, "Asintomática" if sint == "Asintomática" else ("Sintomática" if sint else "")
    if tipo == "viscerales":
        return VISCERAL, datos.get("patologia", "")
    if tipo == "acceso_vascular":
        return ACCESO, (datos.get("cirugia") or "").split(" (")[0]
    if tipo == "varices":
        return VARICES, ""
    if tipo == "congestion_pelvica":
        return PELVICA, ""
    if tipo == "sindrome_postrombotico":
        return POSTROMBOTICO, ""
    if tipo == "trauma":
        return TRAUMA, datos.get("region", "")
    if tipo == "amputacion":
        nivel = datos.get("nivel", "")
        return {
            "Isquemia crónica (CLTI)": (CRONICA, NO_CLAUDICANTE),
            PIE_DIABETICO_SIN_ISQUEMIA: (PIE_DIABETICO, nivel),
            "Isquemia aguda": (AGUDA, ""),
            "Traumatismo": (TRAUMA, ""),
        }.get(ind, (OTROS, "Amputación"))
    if tipo == "miscelanea":
        cat = datos.get("categoria", "")
        if cat == "Aneurisma periférico (no poplíteo)":
            return PERIFERICOS, cat
        if cat == "Infección protésica":
            return INFECCION, cat
        return OTROS, cat
    return OTROS, ""


def meses_entre(desde, hasta):
    """Lista de meses 'AAAA-MM' entre dos meses incluidos."""
    a, m = map(int, desde.split("-"))
    fin = tuple(map(int, hasta.split("-")))
    meses = []
    while (a, m) <= fin and len(meses) < 120:
        meses.append(f"{a:04d}-{m:02d}")
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return meses


def intervenciones(desde, hasta, cirujano_id=None):
    """Intervenciones entre dos meses (incluidos), ya clasificadas."""
    sql = """SELECT p.id, p.tipo, p.fecha_cirugia, p.datos, p.procedimiento_origen_id, pa.codigo, pa.sexo,
                    u.nombre AS cirujano
             FROM procedimientos p
             JOIN pacientes pa ON pa.id = p.paciente_id
             JOIN usuarios u ON u.id = p.cirujano_id
             WHERE substr(p.fecha_cirugia, 1, 7) BETWEEN ? AND ?"""
    params = [desde, hasta]
    if cirujano_id:
        sql += " AND p.cirujano_id = ?"
        params.append(cirujano_id)
    filas = []
    for f in get_db().execute(sql + " ORDER BY p.fecha_cirugia, p.id", params):
        datos = cargar_json(f["datos"])
        patologia, subgrupo = clasificar(f["tipo"], datos)
        filas.append({
            "id": f["id"], "mes": f["fecha_cirugia"][:7], "fecha": f["fecha_cirugia"],
            "codigo": f["codigo"], "sexo": f["sexo"], "cirujano": f["cirujano"],
            "patologia": patologia, "subgrupo": subgrupo,
            "procedimiento": PROCEDIMIENTOS[f["tipo"]]["nombre"],
            "reintervencion": "Sí" if f["procedimiento_origen_id"] else "No",
            "caracter": datos.get("caracter", ""),
            "pie_diabetico": datos.get("pie_diabetico", ""),
        })
    return filas


def resumen(filas, meses):
    """Tablas de recuento por patología (con subgrupos) y por tipo de procedimiento."""
    por_pat = defaultdict(lambda: defaultdict(int))
    por_sub = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    por_proc = defaultdict(lambda: defaultdict(int))
    reint = defaultdict(int)
    for f in filas:
        por_pat[f["patologia"]][f["mes"]] += 1
        if f["subgrupo"]:
            por_sub[f["patologia"]][f["subgrupo"]][f["mes"]] += 1
        por_proc[f["procedimiento"]][f["mes"]] += 1
        if f["reintervencion"] == "Sí":
            reint[f["mes"]] += 1

    def fila(nombre, cuentas, nivel=0):
        valores = [cuentas.get(m, 0) for m in meses]
        return {"nombre": nombre, "valores": valores, "total": sum(valores), "nivel": nivel}

    patologias = []
    for p in PATOLOGIAS:
        if p in por_pat:
            patologias.append(fila(p, por_pat[p]))
            for sub in sorted(por_sub[p]):
                patologias.append(fila(sub, por_sub[p][sub], nivel=1))
    procedimientos = [fila(PROCEDIMIENTOS[k]["nombre"], por_proc[PROCEDIMIENTOS[k]["nombre"]])
                      for k in PROCEDIMIENTOS if PROCEDIMIENTOS[k]["nombre"] in por_proc]
    total = defaultdict(int)
    for f in filas:
        total[f["mes"]] += 1
    return {
        "patologias": patologias,
        "procedimientos": procedimientos,
        "total": fila("Total", total),
        "reintervenciones": fila("De ellas, reintervenciones", reint),
    }
