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
- **14 grupos de procedimiento**, cada uno con su formulario: aorta abierta; EVAR/FEVAR/BEVAR
  (el acceso percutáneo, PEVAR, se registra en el campo de acceso); TEVAR (estándar o con
  rama para la subclavia); bypass; endovascular periférico; acceso vascular; ramas viscerales
  (isquemia mesentérica aguda y crónica, entre otras); carótida (abierta y endovascular);
  congestión venosa pélvica; varices; isquemia aguda/embolectomía (incluye AngioJet);
  traumatismo vascular; amputaciones; misceláneos.
- **Material con medidas.** En los procedimientos endovasculares se registra cada dispositivo
  (tipo, vaso, marca/modelo, diámetro y longitud), además de una descripción libre.
- **Reintervenciones enlazadas.** Una reintervención se registra como una intervención nueva
  unida a la original (motivo y relación). En la ficha del paciente se ven en árbol, y puede
  tener sus propios seguimientos o no. El seguimiento de la intervención original continúa,
  lo que permite calcular la permeabilidad primaria y secundaria y la libertad de reintervención.
- **Resultados a 30 días** en el seguimiento al mes: reingreso y su motivo. La mortalidad a
  30 días se calcula sola en la exportación (columna `mortalidad_30d`).
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
  **registro de auditoría** (accesos, altas, ediciones, exportaciones). Bloqueo temporal
  tras varios intentos de acceso fallidos.

## Probarlo en 5 minutos

Necesitas Python 3.10 o superior.

```bash
cd registro-vascular
python -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

flask --app registro init          # crea instance/config.py (claves) y la base de datos
flask --app registro demo          # OPCIONAL: 25 pacientes ficticios y 3 usuarios de prueba
flask --app registro run           # abre http://localhost:5000 (solo para probar)
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

Si arrancas la aplicación con `python servir.py` (ver más abajo), no necesitas nada de esto:
los recordatorios se envían solos. Solo si usas otro servidor:

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

## Publicarlo en internet

Paso a paso, con un servidor en la UE, dominio propio, HTTPS y copias automáticas:
**[GUIA-PUBLICAR-ONLINE.md](GUIA-PUBLICAR-ONLINE.md)**.

## Instalarlo en tu ordenador con acceso remoto

La idea es que la aplicación y los datos vivan en tu ordenador y que los compañeros entren
desde fuera por un canal cifrado, **sin abrir puertos en el router** y sin que la página
quede visible para el resto de internet.

### 1. Instalar y arrancar

1. Instala Python 3.10 o superior desde [python.org](https://www.python.org/downloads/). En
   Windows, marca «Add Python to PATH».
2. Descarga este repositorio (botón *Code → Download ZIP* en GitHub, o `git clone`) y abre
   una terminal en la carpeta `registro-vascular`.
3. Ejecuta, una sola vez:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate            # Mac/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   flask --app registro init
   flask --app registro crear-usuario --admin
   ```

4. Arranca el servidor con doble clic en `iniciar-registro.bat` (Windows) o
   `iniciar-registro.command` (Mac), o con `python servir.py`. Queda disponible en
   <http://localhost:8080>.

`servir.py` usa un servidor apto para uso real (waitress) y **envía los recordatorios solo**:
cada día, a partir de las 8:00 (`RECORDATORIO_HORA`), o en cuanto se encienda el ordenador si
estaba apagado a esa hora. No hace falta cron ni el Programador de tareas.

Para que arranque al encender el ordenador:
- **Windows:** pulsa Win+R, escribe `shell:startup` y pon ahí un acceso directo a `iniciar-registro.bat`.
- **Mac:** Ajustes del Sistema → General → Ítems de inicio → añade `iniciar-registro.command`.

Configura también el ordenador para que **no se suspenda**: mientras está dormido, nadie
puede acceder a la aplicación.

### 2. Acceso remoto con Tailscale (recomendado)

[Tailscale](https://tailscale.com) crea una red privada cifrada entre los dispositivos que tú
autorices. La aplicación solo es accesible desde esos dispositivos; para el resto de internet
no existe. Es gratis hasta 3 usuarios y 100 dispositivos (plan Personal); para más usuarios
hay planes de pago.

1. Instala Tailscale en tu ordenador e inicia sesión.
2. Publica la aplicación con HTTPS dentro de tu red privada:

   ```bash
   tailscale serve --bg 8080
   ```

   Tailscale te dará una dirección del tipo `https://mi-ordenador.tu-red.ts.net`.
3. En `instance/config.py`, pon esa dirección y activa el modo proxy:

   ```python
   BASE_URL = "https://mi-ordenador.tu-red.ts.net"
   DETRAS_DE_PROXY = True
   SESSION_COOKIE_SECURE = True
   ```

   Después, reinicia `servir.py`.
4. Invita a cada cirujano a tu red de Tailscale (panel de administración → *Users → Invite*).
   Cada uno instala Tailscale en su móvil u ordenador y entra en esa dirección con su usuario
   del registro.

**Pega:** cada compañero tiene que instalar Tailscale. Además, algunas redes de hospital
bloquean las VPN; en ese caso, se conecta desde el móvil con datos o desde casa.

### 3. Alternativa sin instalar nada en los dispositivos: Cloudflare Tunnel + Access

Si prefieres que se entre desde cualquier navegador, [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
publica la aplicación en un dominio tuyo (por ejemplo, `registro.midominio.es`) sin abrir
puertos. **Es imprescindible** protegerla con **Cloudflare Access**: una regla que solo deje
pasar a los correos de tu lista, que reciben un código en el correo antes de ver siquiera la
pantalla de acceso. Así hay dos barreras: el código de Cloudflare y la contraseña del registro.
Necesitas un dominio propio (unos 10 € al año); el plan gratuito de Cloudflare cubre hasta 50 usuarios.

```bash
cloudflared tunnel login
cloudflared tunnel create registro
cloudflared tunnel route dns registro registro.midominio.es
cloudflared tunnel run --url http://localhost:8080 registro
```

Después, en el panel de Cloudflare Zero Trust, crea una *Access application* para
`registro.midominio.es` con una política *Allow* que liste los correos de los cirujanos. En
`config.py`, pon `BASE_URL = "https://registro.midominio.es"`, `DETRAS_DE_PROXY = True` y
`SESSION_COOKIE_SECURE = True`.

> **No hagas** redirección de puertos en el router ni ejecutes `flask run --host 0.0.0.0`
> para acceder desde fuera: la aplicación quedaría expuesta a internet sin cifrar.

### 4. Correo de los recordatorios desde tu ordenador

Fuera de la red del hospital no podrás usar su servidor de correo. Una opción sencilla es
una cuenta de Gmail dedicada (por ejemplo, `registro.vascular.xxx@gmail.com`) con la
verificación en dos pasos activada y una **contraseña de aplicación**:

```python
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = "registro.vascular.xxx@gmail.com"
MAIL_PASSWORD = "contraseña de aplicación de 16 letras"
MAIL_FROM = "registro.vascular.xxx@gmail.com"
```

Los correos solo contienen el código del paciente, el hito y el enlace; no llevan datos clínicos.

### 5. Proteger el ordenador

Los datos están en tu disco, así que:
- **Cifra el disco:** BitLocker en Windows, FileVault en Mac.
- Pon contraseña a tu sesión y bloqueo automático de pantalla.
- **Haz copias de seguridad** cifradas de `instance/` (base de datos y `config.py`) en otro
  soporte. Hazlas con el servidor parado, o copia el fichero con `sqlite3 registro.sqlite3 ".backup copia.sqlite3"`.
- Mantén el sistema y Tailscale o `cloudflared` actualizados.

Aun así, un ordenador personal con datos de pacientes es algo que **debe conocer y autorizar
el DPD del hospital**. Si no lo autoriza, este mismo montaje funciona igual en un PC del
servicio dentro del hospital.

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
  programador.py     envío diario automático de recordatorios
servir.py            arranque para uso real (waitress + recordatorios)
iniciar-registro.*   arranque con doble clic (Windows .bat, Mac .command)
Dockerfile, docker-compose.yml, Caddyfile, instalar-servidor.sh, copia-seguridad.sh
                     publicación en un servidor (ver GUIA-PUBLICAR-ONLINE.md)
  templates/, static/
tests/               pruebas (pytest)
```
