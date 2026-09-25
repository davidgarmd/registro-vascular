# Registro vascular

Prototipo de registro de intervenciones de cirugía vascular con **formularios dinámicos**
y **recordatorios por correo** a cada cirujano a 1, 3, 6 y 12 meses de la cirugía.

> **Este repositorio contiene solo el código.** Los datos de los pacientes (base de datos)
> y las claves de cifrado se guardan en la carpeta `instance/`, que está excluida de git y
> debe quedarse en un ordenador o servidor del hospital.

## Qué hace

- **Pacientes seudonimizados.** Se introduce el NHC, pero se guarda cifrado (para poder
  consultarlo dentro de la aplicación) y como huella HMAC (para buscar y evitar duplicados).
  Cada paciente recibe un código (`RV-00012`), que es lo único que aparece en correos y
  exportaciones. No se piden nombre, DNI ni fecha de nacimiento.
- **11 grupos de procedimiento**, cada uno con su formulario: aorta abierta; EVAR/FEVAR/BEVAR
  (el acceso percutáneo, PEVAR, se registra en el campo de acceso); TEVAR (estándar o con
  rama para la subclavia); bypass; endovascular periférico; acceso vascular; ramas viscerales
  (isquemia mesentérica aguda y crónica, entre otras); carótida (abierta y endovascular);
  congestión venosa pélvica; varices; misceláneos.
- **Formularios dinámicos.** Los campos aparecen u ocultan según lo elegido. Por ejemplo,
  al marcar BEVAR aparecen los vasos diana; al marcar PEVAR, el dispositivo de cierre; al
  elegir carótida endovascular, la protección embólica. El servidor valida con las mismas reglas.
- **Seguimientos automáticos.** Al guardar una cirugía se programan los seguimientos a
  1, 3, 6 y 12 meses. Cada uno tiene su formulario: un bloque común (estado vital,
  reintervención, eventos, tratamiento) y otro propio del procedimiento (endofugas y saco,
  permeabilidad, ITB, reestenosis carotídea, EVA, recurrencia de varices…).
- **Recordatorios.** Un proceso diario envía a cada cirujano responsable **un único correo**
  con sus seguimientos vencidos. El aviso se repite cada 7 días, con un máximo de 4. Los
  correos no llevan datos clínicos: solo el código, el hito y un enlace. Si un seguimiento
  no puede hacerse, se marca como «no realizable» y deja de avisar.
- **Exportación a CSV** por procedimiento (cirugías y seguimientos), lista para Excel, SPSS o R.
- **Usuarios con contraseña**, roles de cirujano y administrador, protección CSRF y un
  **registro de auditoría** (accesos, altas, ediciones, exportaciones).

## Probarlo en 5 minutos

Necesitas Python 3.10 o superior.

```bash
cd registro-vascular
python -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

flask --app registro init          # crea instance/config.py (claves) y la base de datos
flask --app registro demo          # OPCIONAL: 25 pacientes ficticios y 3 usuarios de prueba
flask --app registro run           # abre http://localhost:5000
```

Usuarios de la demo: `admin@demo.local`, `cirujana1@demo.local`, `cirujano2@demo.local`.
Contraseña: `demo-registro-2026`.

Para empezar con datos reales, borra la carpeta `instance/`, vuelve a ejecutar `init` y
crea el primer usuario administrador:

```bash
flask --app registro crear-usuario --admin
```

Los demás usuarios se crean desde la web (menú **Usuarios**).

## Recordatorios por correo

Mientras `MAIL_SERVER` esté vacío (modo prueba), los correos se guardan como ficheros
`.eml` en `instance/outbox/`. Para enviarlos de verdad, edita `instance/config.py`:

```python
BASE_URL = "http://registro-vascular.hospital.local:5000"   # dirección que usan los cirujanos
MAIL_SERVER = "smtp.hospital.es"     # pide a Informática el relay SMTP interno
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = "..."
MAIL_PASSWORD = "..."
MAIL_FROM = "registro-vascular@hospital.es"
```

Programa el envío una vez al día:

- **Linux (cron):** `0 8 * * * cd /ruta/registro-vascular && .venv/bin/flask --app registro enviar-recordatorios`
- **Windows (Programador de tareas):** acción `C:\ruta\registro-vascular\.venv\Scripts\flask.exe`,
  argumentos `--app registro enviar-recordatorios`, iniciar en `C:\ruta\registro-vascular`.

Para probar sin esperar meses: `flask --app registro enviar-recordatorios --fecha 2027-01-01`.
Los administradores también tienen un botón **Enviar recordatorios ahora** en la página de inicio.

## Cambiar los formularios

Todas las variables están en [`registro/formularios.py`](registro/formularios.py). Cada campo
se define en una línea, por ejemplo:

```python
C("cierre_percutaneo", "Dispositivo de cierre", "select",
  ["ProGlide (preclose)", "MANTA", "Otro"], si=si("acceso", *_percutaneo)),
```

Los datos se guardan como JSON, así que añadir o quitar campos no requiere tocar la base de
datos. Si renombras una opción, los registros antiguos conservan el texto anterior.
Después de cambiar algo, ejecuta las pruebas (`pip install -r requirements-dev.txt && pytest`):
comprueban, entre otras cosas, que ninguna condición apunte a un campo o valor inexistente.

## Dónde instalarlo

| Opción | Para qué |
|---|---|
| Tu ordenador (`flask run`) | Probar y enseñar el prototipo, con datos ficticios. |
| PC o servidor del hospital, en la intranet | **Recomendada para datos reales.** Los datos no salen de la red del hospital. Pide a Informática una máquina, un nombre interno y el relay SMTP. En producción, usa un servidor WSGI (`pip install waitress` y `waitress-serve --port 8080 --call registro:create_app`) y HTTPS (`SESSION_COOKIE_SECURE = True`). |
| Nube (VPS en la UE) | Solo con el visto bueno del DPD y un contrato de encargado del tratamiento. |

**Copias de seguridad:** guarda `instance/registro.sqlite3` **y** `instance/config.py`.
Sin `config.py` (la clave `NHC_KEY`), los NHC guardados no pueden descifrarse.

## Protección de datos

El NHC es un dato **seudonimizado**, no anónimo: los datos siguen siendo datos de salud según
el RGPD. Antes de usarlo con pacientes reales:

1. Consulta al **Delegado de Protección de Datos** del hospital (registro de actividades de
   tratamiento y, si procede, evaluación de impacto).
2. Si los datos se van a usar para investigar o publicar, pide la aprobación del **CEIm**.
3. No subas nunca la carpeta `instance/` ni exportaciones CSV al repositorio.

## Limitaciones del prototipo

- No hay recuperación de contraseña por correo: la restablece un administrador.
- No hay bloqueo tras intentos de acceso fallidos (los intentos quedan en la auditoría).
- SQLite basta para un servicio (miles de registros y varios usuarios a la vez). Para un
  registro multicéntrico, convendría migrar a PostgreSQL.
- Cualquier usuario puede ver y editar los registros del servicio; queda constancia en la auditoría.

## Estructura

```
registro/
  formularios.py     definición de los 11 formularios y de los seguimientos
  modelos.py         pacientes, intervenciones y seguimientos
  recordatorios.py   selección de pendientes y envío de correos
  seguridad.py       cifrado y HMAC del NHC
  auth.py            acceso, usuarios y CSRF
  vistas.py          páginas y exportación
  cli.py             comandos: init, crear-usuario, enviar-recordatorios, demo
  templates/, static/
tests/               pruebas (pytest)
```
