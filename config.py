import os
from dotenv import load_dotenv

# Carga las variables desde el archivo .env
load_dotenv()

# Configuración de AWS
AWS_S3_BUCKET = "aws-secret-key"
AWS_REGION = "us-east-2"
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")

# Configuración de RDS
RDS_HOST = "localhost"
RDS_DB = "db_cloud_image"
RDS_USER = "postgres"
RDS_PASSWORD = os.getenv("RDS_PASSWORD")

# Configuración de Imagga
IMAGGA_API_KEY = os.getenv("IMAGGA_API_KEY")
IMAGGA_API_SECRET = os.getenv("IMAGGA_API_SECRET")
IMAGGA_ENDPOINT = "https://api.imagga.com/v2/tags"
