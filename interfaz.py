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
    
    # Extraemos el nombre que la persona escribió en el formulario
    nombre_usuario = datos.get('nombre', 'Empleado').strip().replace(" ", "_")
    
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

    # Asignamos los nombres personalizados para las descargas
    nombre_archivo_pdf = f"Carta_Retiro_Cesantias_{nombre_usuario}.pdf"
    nombre_archivo_docx = f"Carta_Retiro_Cesantias_{nombre_usuario}.docx"

    # Intentamos enviar el PDF si existe
    if ruta_pdf and os.path.exists(ruta_pdf):
        return send_file(ruta_pdf, as_attachment=True, download_name=nombre_archivo_pdf)
    else:
        # Si aún no descarga en PDF, te bajará el Word limpio con el formato correcto
        return send_file(ruta_docx, as_attachment=True, download_name=nombre_archivo_docx)
