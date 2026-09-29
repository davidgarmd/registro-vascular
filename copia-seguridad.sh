#!/bin/bash
# Copia de seguridad diaria del registro (la programa instalar-servidor.sh a las 3:00).
# Guarda la base de datos y las claves en ./copias y borra las copias de más de 30 días.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p copias
chmod 700 copias
fecha=$(date +%F)
# Copia en caliente y consistente (la aplicación puede seguir funcionando).
python3 -c "import sqlite3,sys; o=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); o.backup(d); d.close()" \
  datos/registro.sqlite3 "copias/registro-$fecha.sqlite3"
cp datos/config.py "copias/config-$fecha.py"
find copias -type f -mtime +30 -delete
echo "Copia creada: copias/registro-$fecha.sqlite3"
