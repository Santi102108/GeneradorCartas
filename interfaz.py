import os
from flask import Flask, render_template, request, send_file, after_this_request
from generador import generar_carta_cesantias

app = Flask(__name__)

@app.route("/")
def index():
    # Se corrige pasando datos={} para que index.html cargue sin errores la primera vez
    return render_template("index.html", datos={})

@app.route("/generar", methods=["POST"])
def generar():
    datos = request.form.to_dict()
    ruta_docx, ruta_pdf = generar_carta_cesantias(datos)

    @after_this_request
    def eliminar_temporales(response):
        try:
            if ruta_docx and os.path.exists(ruta_docx):
                os.remove(ruta_docx)
            if ruta_pdf and os.path.exists(ruta_pdf):
                os.remove(ruta_pdf)
        except Exception as e:
            print(f"Error limpiando archivos: {e}")
        return response

    if ruta_pdf and os.path.exists(ruta_pdf):
        return send_file(ruta_pdf, as_attachment=True, download_name="Carta_Retiro_Cesantias.pdf")
    else:
        return send_file(ruta_docx, as_attachment=True, download_name="Carta_Retiro_Cesantias.docx")
