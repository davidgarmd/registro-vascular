# Guía para publicar el registro en internet

Con esta guía, el registro queda accesible en una dirección propia, por ejemplo
`https://registro.midominio.es`, desde cualquier ordenador o móvil, con HTTPS y
recordatorios por correo. Se hace en unos 45 minutos y no hace falta saber programar:
basta con copiar y pegar los comandos.

**Coste aproximado:** 5-8 € al mes (servidor y copias de seguridad) más unos 10 € al año (dominio).

> ⚠️ **Antes de introducir pacientes reales**, lee el apartado
> [Protección de datos](#protección-de-datos-antes-de-meter-pacientes-reales). Para montarlo y
> probarlo con datos ficticios no hace falta ningún permiso.

---

## Qué vas a montar

```
Cirujanos (navegador, móvil)
        │  HTTPS (cifrado)
        ▼
Servidor en la UE (Hetzner, Alemania/Finlandia)
 ├─ Caddy: certificado HTTPS automático y cabeceras de seguridad
 ├─ Aplicación del registro (Docker)
 ├─ Base de datos y claves (carpeta datos/)
 └─ Copia de seguridad diaria (3:00) + copias automáticas de Hetzner
```

Lo que ya está incluido:
- HTTPS obligatorio: si alguien entra por `http://`, se le redirige a `https://`.
- Cortafuegos con solo tres puertos abiertos: SSH, HTTP y HTTPS.
- Bloqueo durante 15 minutos tras 5 contraseñas erróneas en una cuenta, o 20 desde una misma IP.
- Bloqueo automático de quien intente adivinar la contraseña de acceso al servidor (fail2ban).
- Parches de seguridad del sistema instalados solos.
- Recordatorios diarios y copia de seguridad diaria, sin que tengas que hacer nada.

---

## Paso 1. Crear el servidor (Hetzner, unos 10 minutos)

Hetzner es un proveedor alemán con centros de datos en la UE y contrato RGPD (encargado del
tratamiento) disponible en su panel. Cualquier otro VPS europeo con Ubuntu 24.04 sirve igual:
OVH, IONOS, Scaleway…

1. Crea una cuenta en <https://www.hetzner.com/cloud> y verifica tu identidad.
2. **Prepara una llave SSH.** Es más segura que una contraseña para entrar al servidor.
   - Abre **Símbolo del sistema** (Windows) o **Terminal** (Mac) y escribe:
     ```
     ssh-keygen -t ed25519
     ```
     Pulsa Intro en todas las preguntas. Puedes poner una frase de paso si quieres.
   - Muestra la llave pública para copiarla:
     - Windows: `type %USERPROFILE%\.ssh\id_ed25519.pub`
     - Mac: `cat ~/.ssh/id_ed25519.pub`

     Copia la línea entera, la que empieza por `ssh-ed25519`.
3. En la consola de Hetzner, crea un proyecto (por ejemplo, «Registro vascular») y pulsa **Add Server**:
   - **Location:** Falkenstein, Núremberg o Helsinki (todas en la UE).
   - **Image:** Ubuntu 24.04.
   - **Type:** el más pequeño de tipo *Shared vCPU* (x86). Es suficiente de sobra.
   - **SSH keys:** *Add SSH key* → pega la línea que copiaste.
   - **Backups:** actívalo. Cuesta un 20 % más y guarda una copia completa del servidor cada día.
   - **Name:** `registro-vascular`.
4. Pulsa **Create & Buy now** y apunta la **dirección IPv4** del servidor (algo como `168.119.x.x`).

## Paso 2. Comprar el dominio y apuntarlo al servidor (unos 10 minutos)

1. Compra un dominio en cualquier registrador: DonDominio, Namecheap, Cloudflare,
   IONOS… Por ejemplo, `registrovascular.es`.
2. En el panel **DNS** del registrador, crea un registro:
   - **Tipo:** `A`
   - **Nombre/Host:** `registro` (quedará `registro.registrovascular.es`), o `@` si quieres usar el dominio sin prefijo.
   - **Valor:** la IPv4 del servidor.
3. Espera unos minutos. Para comprobar que ya apunta bien, escribe en tu ordenador
   `ping registro.registrovascular.es`: debe responder la IP del servidor.

## Paso 3. Preparar la cuenta de correo que enviará los recordatorios (unos 5 minutos)

1. Crea una cuenta de Gmail solo para esto, por ejemplo `registro.vascular.hgucr@gmail.com`.
2. Activa la **verificación en dos pasos**: <https://myaccount.google.com/security>.
3. Crea una **contraseña de aplicación**: <https://myaccount.google.com/apppasswords>. Ponle de nombre
   «Registro» y copia las 16 letras que te da.

Los correos solo llevan el código del paciente, el hito y el enlace: ni el NHC ni datos clínicos.
Puedes saltarte este paso y configurar el correo más adelante.

## Paso 4. Instalar el registro en el servidor (unos 15 minutos)

1. Conéctate al servidor desde tu ordenador:
   ```
   ssh root@IP_DEL_SERVIDOR
   ```
   La primera vez te pregunta si confías en el servidor: escribe `yes`.
2. Descarga el programa y lanza el instalador:
   ```
   git clone -b claude/surgical-data-collection-system-on57lv https://github.com/davidgarmd/Claude.git
   cd Claude/registro-vascular
   bash instalar-servidor.sh
   ```
3. El instalador te preguntará:
   - el **dominio** (`registro.registrovascular.es`);
   - **tu correo** (para los avisos del certificado HTTPS);
   - la **cuenta de Gmail** y la **contraseña de aplicación** del paso 3 (puedes dejarlas vacías).

   Después actualiza el sistema, instala Docker, configura el cortafuegos, arranca la aplicación
   y programa las copias. Tarda unos minutos.
4. Crea tu usuario administrador:
   ```
   docker compose exec app flask --app registro crear-usuario --admin
   ```
5. Abre `https://registro.registrovascular.es` en el navegador y entra con ese usuario. Desde el menú
   **Usuarios**, da de alta a los demás cirujanos con su correo del hospital; ese es el correo
   al que les llegarán los recordatorios.

Si el navegador muestra un aviso de certificado justo al terminar, espera 1-2 minutos: Caddy
lo está pidiendo a Let's Encrypt.

---

## Uso diario y mantenimiento

Para cualquiera de estas tareas, conéctate primero con `ssh root@IP_DEL_SERVIDOR` y
entra en la carpeta con `cd Claude/registro-vascular`.

| Quiero… | Comando |
|---|---|
| Ver si está funcionando | `docker compose ps` |
| Ver los mensajes de la aplicación (errores, recordatorios enviados) | `docker compose logs --tail 50 app` |
| Reiniciarla | `docker compose restart` |
| Instalar una versión nueva del programa | `git pull && docker compose up -d --build` |
| Enviar los recordatorios ya (sin esperar a mañana) | `docker compose exec app flask --app registro enviar-recordatorios` |
| Hacer una copia de seguridad ahora | `./copia-seguridad.sh` |
| Cambiar el correo o la hora de los recordatorios | `nano .env` (guardar con Ctrl+O y salir con Ctrl+X) y después `docker compose up -d` |

### Copias de seguridad

Hay tres niveles de copia:
1. **Diaria en el propio servidor**, a las 3:00, en la carpeta `copias/`. Se guardan 30 días.
2. **Diaria de todo el servidor**, la que hace Hetzner si activaste *Backups* en el paso 1.
3. **Fuera del servidor**: descárgala tú de vez en cuando, por ejemplo una vez al mes. Desde tu
   ordenador, sin conectarte por SSH:
   ```
   scp -r root@IP_DEL_SERVIDOR:Claude/registro-vascular/copias ./copias-registro
   ```
   Guárdala en un disco o carpeta cifrados. Cada copia incluye la base de datos **y** el fichero
   `config-*.py` con las claves: sin ese fichero, los NHC no se pueden descifrar.

### Restaurar una copia

```
docker compose stop app
cp copias/registro-AAAA-MM-DD.sqlite3 datos/registro.sqlite3
cp copias/config-AAAA-MM-DD.py datos/config.py
chown 1000:1000 datos/*
docker compose start app
```

---

## Seguridad adicional recomendada (opcional)

Si quieres que solo los correos de tu lista puedan **ver siquiera** la pantalla de acceso,
pon **Cloudflare Access** delante. Es gratis hasta 50 usuarios y cada cirujano recibe un código
por correo antes de ver el registro, así que funciona como un segundo factor. Requiere pasar la
gestión DNS del dominio a Cloudflare; la configuración está en
<https://developers.cloudflare.com/cloudflare-one/applications/configure-apps/self-hosted-public-app/>.

---

## Protección de datos (antes de meter pacientes reales)

Técnicamente, todo lo anterior funciona. Lo que queda es el **permiso** para usarlo con
datos reales. El NHC es un dato **seudonimizado**, no anónimo, así que la información sigue
siendo un dato de salud según el RGPD. El responsable del tratamiento es el hospital, no tú
a título personal, y el hospital tiene que autorizarlo.

Lleva a tu **Delegado de Protección de Datos (DPD)** esta información:

1. **Qué datos se recogen:** NHC (cifrado), sexo, edad y variables clínicas del procedimiento y del
   seguimiento. No se recogen nombre, DNI ni fecha de nacimiento.
2. **Dónde se guardan:** servidor de Hetzner Online GmbH en Alemania o Finlandia (UE). Hetzner
   ofrece un contrato de encargado del tratamiento (*AVV/DPA*), que se firma en su consola:
   *Account → Data Privacy*.
3. **Medidas de seguridad:** HTTPS; NHC cifrado (AES) y huella HMAC para búsquedas; claves fuera de
   la base de datos; usuarios con contraseña y bloqueo por intentos fallidos; registro de
   auditoría de accesos, cambios y exportaciones; cortafuegos; parches automáticos; copias diarias;
   correos y exportaciones sin NHC.
4. **Finalidad:** seguimiento de resultados quirúrgicos del servicio. Si además se va a
   investigar o publicar, hace falta la **aprobación del CEIm**.

Es posible que el DPD pida una **evaluación de impacto (EIPD)**, que el tratamiento se incluya
en el **registro de actividades de tratamiento**, o que el servidor cumpla el **Esquema Nacional
de Seguridad (ENS)**, que suelen exigir las administraciones sanitarias públicas. Si el hospital
prefiere que los datos no salgan de su red, esta misma instalación funciona sin cambios en un
servidor Ubuntu del hospital: Informática solo tiene que seguir el paso 4 y darle un nombre
interno.

**Nota sobre el repositorio:** el código está en un repositorio **público** de GitHub. Es
correcto porque solo contiene el programa, nunca datos ni claves. Si prefieres que sea
privado, cámbialo en *Settings → General → Danger zone → Change visibility*. En ese caso,
para el `git clone` del paso 4 necesitarás un *token* de acceso de GitHub.
