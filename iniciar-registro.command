#!/bin/bash
# Doble clic para arrancar el registro en Mac (o ./iniciar-registro.command en Linux).
cd "$(dirname "$0")"
source .venv/bin/activate
python servir.py
