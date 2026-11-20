"""Aplicación web: una respuesta PDF por solicitud, sin datos compartidos."""
from io import BytesIO
import re
from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import BadRequest
from generador import generar_pdf, validar_datos
from utilidades import convertir_numero_a_palabras

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


def _nombre_archivo(datos):
    nombre = re.sub(r"[^A-Za-z0-9_-]+", "_", datos["nombre"]).strip("_")[:55] or "Empleado"
    cedula = re.sub(r"\D", "", datos["cedula"])[:25]
    return f"Carta_Cesantias_{nombre}_{cedula}.pdf"


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/valor-letras")
def valor_letras():
    try:
        cuerpo = request.get_json(silent=True) or {}
        return jsonify({"texto": convertir_numero_a_palabras(cuerpo.get("valor", ""))})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/generar")
def generar():
    try:
        datos = validar_datos(request.form.to_dict())
        contenido = generar_pdf(datos)
        vista_previa = request.form.get("preview") == "1"
        respuesta = send_file(
            BytesIO(contenido), mimetype="application/pdf",
            as_attachment=not vista_previa,
            download_name=_nombre_archivo(datos), conditional=False)
        respuesta.headers["Cache-Control"] = "no-store, private"
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        return respuesta
    except (ValueError, BadRequest) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Error al generar PDF")
        return jsonify({"error": "No se pudo generar el PDF. Verifique la configuración de conversión."}), 503


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
