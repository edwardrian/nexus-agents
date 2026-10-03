# 1. Imagen base oficial ligera
FROM python:3.13-slim

# 2. Variables de entorno recomendadas para Python en contenedores
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Directorio de trabajo dentro del contenedor
WORKDIR /app

# 4. Copiar el archivo de dependencias primero (aprovecha la caché de Docker)
COPY requirements.txt .

# 5. Instalar dependencias sin guardar la caché del instalador
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el resto del código del proyecto
COPY . .

# 7. Crear y usar un usuario sin privilegios por seguridad
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

# 8. Puerto donde escucha tu app (ej. 8000 para FastAPI/Django, 5000 para Flask)
EXPOSE 8000

# 9. Comando de arranque (elige el correspondiente a tu app)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Si usas FastAPI / Uvicorn:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# Si usas Gunicorn (Django/Flask):
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:application"]
