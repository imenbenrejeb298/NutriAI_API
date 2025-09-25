# Image Python légère
FROM python:3.11-slim

# Empêche le buffering des logs
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dossier de travail
WORKDIR /app

# Dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code de l'app
COPY . .

# Render fournit le port via la variable d'env $PORT
EXPOSE 10000

# Commande de démarrage : utilise $PORT si présent, sinon 10000
CMD ["/bin/sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
