from flask import Flask, render_template, request, send_file
from pathlib import Path

from generador import generar_carta

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
PLANTILLA = BASE_DIR / "plantilla.docx"
CARPETA_DESTINO = BASE_DIR / "Documentos Generados"

ultimo_word = None
ultimo_pdf = None


@app.route("/", methods=["GET", "POST"])
def inicio():
    global ultimo_word, ultimo_pdf

    mensaje = ""
    datos = {
        "nombre": "",
        "cedula": "",
        "valor": "",
        "fecha_maxima": "",
        "fecha_expedicion": "",
    }

    if request.method == "POST":

        datos = {
            "nombre": request.form["nombre"],
            "cedula": request.form["cedula"],
            "valor": request.form["valor"],
            "fecha_maxima": request.form["fecha_maxima"],
            "fecha_expedicion": request.form["fecha_expedicion"],
        }

        try:
            ultimo_word, ultimo_pdf = generar_carta(
                datos,
                PLANTILLA,
                CARPETA_DESTINO
            )

            mensaje = "Carta generada correctamente."

        except Exception as e:
            mensaje = str(e)

    return render_template(
        "index.html",
        datos=datos,
        mensaje=mensaje,
        word=ultimo_word,
        pdf=ultimo_pdf
    )


@app.route("/descargar/word")
def descargar_word():
    return send_file(ultimo_word, as_attachment=True)


@app.route("/descargar/pdf")
def descargar_pdf():
    return send_file(ultimo_pdf, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)