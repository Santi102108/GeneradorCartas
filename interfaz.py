import os
from flask import Flask, render_template, request, send_file, after_this_request
from generador import generar_carta_cesantias

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", datos={})

@app.route("/generar", methods=["POST"])
def generar():
    datos = request.form.to_dict()
    nombre_usuario = datos.get('nombre', 'Empleado').strip().replace(" ", "_")
    
    try:
        # Genera los archivos y fuerza la conversión a PDF
        ruta_docx, ruta_pdf = generar_carta_cesantias(datos)

        @after_this_request
        def eliminar_temporales(response):
            try:
                if ruta_docx and os.path.exists(ruta_docx):
                    os.remove(ruta_docx)
                if ruta_pdf and os.path.exists(ruta_pdf):
                    os.remove(ruta_pdf)
            except Exception as e:
                print(f"Error limpiando archivos temporales: {e}")
            return response

        nombre_archivo_pdf = f"Carta_Retiro_Cesantias_{nombre_usuario}.pdf"

        # Obliga al sistema a retornar únicamente el archivo PDF
        if ruta_pdf and os.path.exists(ruta_pdf):
            return send_file(ruta_pdf, as_attachment=True, download_name=nombre_archivo_pdf)
        else:
            return "El archivo PDF no se pudo generar correctamente en el servidor.", 500

    except Exception as error_general:
        return f"Error en la generación del PDF: {str(error_general)}. Asegúrate de que la variable CLOUDCONVERT_API_KEY esté bien configurada en Render.", 500
