# Dockerfile (simple HTTP server)
FROM python:3.11-slim
WORKDIR /app
COPY . .
# Render fournit $PORT en variable d'env, ton main.py l'utilise déjà.
CMD ["python", "main.py"]
