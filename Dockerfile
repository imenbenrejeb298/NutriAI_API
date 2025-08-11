# Image légère Python
FROM python:3.11-slim

# Ne pas créer de fichiers .pyc et forcer les logs en direct
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Render te fournit PORT via la variable d'env
ENV PORT=8080
EXPOSE 8080

WORKDIR /app
COPY main.py /app/

# Pas de requirements: on n'utilise que la lib standard (http.server)
# Démarrage
CMD ["python", "main.py"]
