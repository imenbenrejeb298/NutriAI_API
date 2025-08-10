# Image légère Python
FROM python:3.11-slim

# Crée un dossier de travail
WORKDIR /app

# Copie l'API
COPY main.py /app/main.py

# Port utilisé par l’API
EXPOSE 8080

# Démarrage
CMD ["python", "main.py"]
