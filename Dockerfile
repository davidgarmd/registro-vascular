FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY registro registro
COPY servir.py .

RUN useradd --system --uid 1000 registro && mkdir -p /app/instance && chown registro /app/instance
USER registro

# Base de datos, claves y correos de prueba: se guardan fuera del contenedor.
VOLUME /app/instance
EXPOSE 8080

# `init` es idempotente: crea las claves la primera vez y conserva las existentes.
CMD ["sh", "-c", "flask --app registro init && exec python servir.py --host 0.0.0.0 --puerto 8080"]
