# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Code
COPY . .

# Info : Render injecte $PORT. Par défaut, 10000 en local.
EXPOSE 10000

# Démarrage : on cible asgi:app (au lieu de main:app)
CMD ["/bin/sh","-lc","uvicorn asgi:app --host 0.0.0.0 --port ${PORT:-10000}"]
