from flask import Flask, request, render_template, redirect, url_for, flash
import boto3
import uuid
from config import AWS_S3_BUCKET, AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY, IMAGGA_API_KEY, IMAGGA_API_SECRET, IMAGGA_ENDPOINT
from database import execute_query
from pathlib import Path
import requests
import json

app = Flask(__name__)
app.config.from_pyfile("config.py")

# Configuración del cliente S3
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

# Ruta principal
@app.route("/")
def index():
    return render_template("index.html")

# Página de carga de memes
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        # Obtener datos del formulario
        description = request.form["description"]
        user_alias = request.form["user_alias"]
        custom_tags = request.form["tags"]
        image = request.files["image"]

        # Subir imagen a S3
        image_id = str(uuid.uuid4())
        # Obtener la extensión
        file_extension = Path(image.filename).suffix
        image_path = f"memes/{image_id}{file_extension}"
        s3_client.upload_fileobj(image, AWS_S3_BUCKET, image_path)

        # Insertar en la tabla `memes`
        query = """
        INSERT INTO memes (id, description, path, user_alias, uploaded_at)
        VALUES (%s, %s, %s, %s, NOW())
        """
        execute_query(query, (image_id, description, image_path, user_alias))

        # Obtener etiquetas automáticas de Imagga
        try:
            response = requests.get(
                IMAGGA_ENDPOINT,
                params={"image_url": f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{image_path}"},
                auth=(IMAGGA_API_KEY, IMAGGA_API_SECRET)
            )
            # Verifica si la respuesta fue exitosa
            if response.status_code == 200:
                try:
                    # Convierte el contenido de la respuesta a un diccionario
                    response_data = json.loads(response.text)

                    # Verifica si 'result' y 'tags' están presentes en la respuesta
                    result = response_data.get("result", {})
                    tags = result.get("tags", [])

                    # Si hay etiquetas, las insertamos en la base de datos
                    if tags:
                        for tag in tags:
                            tag_id = str(uuid.uuid4())  # Genera un UUID único
                            confidence = tag["confidence"]
                            tag_name = tag["tag"]["en"]  # Obtén el nombre de la etiqueta

                            # Aquí va tu función para insertar en la base de datos
                            execute_query(
                                """
                                INSERT INTO tags (id, meme_id, tag, confidence)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (tag_id, image_id, tag_name, confidence)
                            )
                    else:
                        print("No se encontraron etiquetas en la respuesta.")
                except ValueError as e:
                    print("Error al procesar la respuesta JSON de Imagga:", e)
                    print("Contenido de la respuesta:", response.text)
                tags = []
            else:
                print(f"Error en la solicitud de Imagga: {response.status_code}")
                print("Contenido de la respuesta:", response.text)
                tags = []
        except Exception as e :
             print(f"Ocurrió un error al hacer la solicitud: {e}")
             tags = []

        # Redirigir a la página principal
        return redirect(url_for("index"))

    return render_template("upload.html")


# Página de búsqueda
@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        keyword = request.form["keyword"]

        # Buscar en las tablas `memes` y `tags`
        query = """
        SELECT memes.id, memes.description, memes.path
        FROM memes
        INNER JOIN tags ON memes.id = tags.meme_id
        WHERE memes.description ILIKE %s OR tags.tag ILIKE %s
        GROUP BY memes.id, memes.description, memes.path
        """
        results = execute_query(query, (f"%{keyword}%", f"%{keyword}%"), fetch=True)

        return render_template("search.html", results=results)
    
    flash("No se a encontrado ningun registro por favor intentelo nuevamente.", "error")
    return render_template("search.html", results=[])

# Página de detalles del meme
@app.route("/meme/<meme_id>")
def meme_details(meme_id):
    query = "SELECT description, path FROM memes WHERE id = %s"
    meme = execute_query(query, (meme_id,), fetch=True)[0]

    query = "SELECT tag, confidence FROM tags WHERE meme_id = %s"
    tags = execute_query(query, (meme_id,), fetch=True)

    return render_template("details.html", meme=meme, tags=tags, AWS_S3_BUCKET=app.config["AWS_S3_BUCKET"],
        AWS_REGION=app.config["AWS_REGION"])

if __name__ == "__main__":
    app.run(debug=True)
