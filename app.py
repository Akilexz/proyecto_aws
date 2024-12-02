from flask import Flask, request, render_template, redirect, url_for
import boto3
import uuid
from config import AWS_S3_BUCKET, AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY, IMAGGA_API_KEY, IMAGGA_API_SECRET, IMAGGA_ENDPOINT
from database import execute_query
import requests

app = Flask(__name__)

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
        image_path = f"memes/{image_id}.jpg"
        s3_client.upload_fileobj(image, AWS_S3_BUCKET, image_path)

        # Insertar en la tabla `memes`
        query = """
        INSERT INTO memes (id, description, path, user_alias, uploaded_at)
        VALUES (%s, %s, %s, %s, NOW())
        """
        execute_query(query, (image_id, description, image_path, user_alias))

        # Obtener etiquetas automáticas de Imagga
        response = requests.get(
            IMAGGA_ENDPOINT,
            headers={"Authorization": f"Basic {IMAGGA_API_KEY}:{IMAGGA_API_SECRET}"},
            params={"image_url": f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{image_path}"},
            auth=({IMAGGA_API_KEY},{IMAGGA_API_SECRET})
        )
        # Verifica si la respuesta fue exitosa
        if response.status_code == 200:
            try:
                # Intenta obtener las etiquetas
                tags = response.json().get("result", {}).get("tags", [])
            except ValueError as e:
                print("Error al procesar la respuesta JSON de Imagga:", e)
                print("Contenido de la respuesta:", response.text)
            tags = []
        else:
            print(f"Error en la solicitud de Imagga: {response.status_code}")
            print("Contenido de la respuesta:", response.text)
            tags = []

        # Insertar etiquetas en la tabla `tags`
        for tag in tags:
            tag_id = str(uuid.uuid4())
            confidence = tag["confidence"]
            tag_name = tag["tag"]["en"]
            execute_query(
                """
                INSERT INTO tags (id, meme_id, tag, confidence)
                VALUES (%s, %s, %s, %s)
                """,
                (tag_id, image_id, tag_name, confidence)
            )

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
        LEFT JOIN tags ON memes.id = tags.meme_id
        WHERE memes.description ILIKE %s OR tags.tag ILIKE %s
        """
        results = execute_query(query, (f"%{keyword}%", f"%{keyword}%"), fetch=True)

        return render_template("search.html", results=results)

    return render_template("search.html", results=[])

# Página de detalles del meme
@app.route("/meme/<meme_id>")
def meme_details(meme_id):
    query = "SELECT description, path FROM memes WHERE id = %s"
    meme = execute_query(query, (meme_id,), fetch=True)[0]

    query = "SELECT tag, confidence FROM tags WHERE meme_id = %s"
    tags = execute_query(query, (meme_id,), fetch=True)

    return render_template("details.html", meme=meme, tags=tags)

if __name__ == "__main__":
    app.run(debug=True)
