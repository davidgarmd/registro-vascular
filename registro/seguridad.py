"""Seudonimización del número de historia clínica (NHC).

- Se guarda un HMAC-SHA256 del NHC normalizado: permite buscar y detectar
  duplicados sin tener el NHC en claro.
- Se guarda el NHC cifrado (Fernet/AES) para que un usuario autenticado pueda
  ver a qué paciente corresponde un código. Nunca aparece en correos ni en
  exportaciones.

Las claves viven en instance/config.py (o en variables de entorno), nunca en
la base de datos ni en el repositorio. Si se pierde NHC_KEY, los NHC dejan de
poder descifrarse.
"""
import hashlib
import hmac
import re

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


def normalizar_nhc(nhc):
    return re.sub(r"[\s\-./]", "", nhc or "").upper()


def _clave(nombre):
    valor = current_app.config.get(nombre)
    if not valor:
        raise RuntimeError(f"Falta {nombre}. Ejecuta: flask --app registro init")
    return valor.encode() if isinstance(valor, str) else valor


def nhc_hmac(nhc):
    return hmac.new(_clave("HMAC_KEY"), normalizar_nhc(nhc).encode(), hashlib.sha256).hexdigest()


def cifrar_nhc(nhc):
    return Fernet(_clave("NHC_KEY")).encrypt(normalizar_nhc(nhc).encode()).decode()


def descifrar_nhc(token):
    try:
        return Fernet(_clave("NHC_KEY")).decrypt(token.encode()).decode()
    except InvalidToken:
        return "(no descifrable: clave distinta)"
