# Usar una imagen base de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar los archivos necesarios dentro del contenedor
COPY . /app

# Instalar las dependencias necesarias (incluyendo boto3)
RUN pip install --no-cache-dir -r requirements.txt

# Si no usas un archivo requirements.txt, puedes instalar boto3 directamente:
# RUN pip install boto3

# Exponer el puerto en el que Flask está ejecutándose
EXPOSE 5000

# Definir el comando para ejecutar la aplicación
CMD ["python", "app.py"]
