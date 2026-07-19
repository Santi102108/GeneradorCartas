import os
from pathlib import Path
from docx import Document
import cloudconvert

from utilidades import convertir_numero_a_palabras, formatear_fecha_larga

API_KEY = os.environ.get("CLOUDCONVERT_API_KEY")
if API_KEY:
    cloudconvert.configure(api_key=API_KEY)

def convertir_docx_a_pdf_cloudconvert(ruta_docx, ruta_pdf):
    if not API_KEY:
        raise ValueError("La variable CLOUDCONVERT_API_KEY no está configurada.")

    job = cloudconvert.Job.create(payload={
        "tasks": {
            "importar-docx": {"operation": "import/upload"},
            "convertir-a-pdf": {
                "operation": "convert",
                "input": "importar-docx",
                "output_format": "pdf",
                "engine": "office"
            },
            "exportar-pdf": {"operation": "export/url", "input": "convertir-a-pdf"}
        }
    })

    upload_task = None
    for task in job["tasks"]:
        if task["name"] == "importar-docx":
            upload_task = task

    cloudconvert.Task.upload(file_name=ruta_docx, task=upload_task)
    completed_job = cloudconvert.Job.wait(id=job["id"])

    export_task = None
    for task in completed_job["tasks"]:
        if task["name"] == "exportar-pdf":
            export_task = task

    if export_task["status"] == "finished" and export_task["result"]["files"]:
        archivo_salida = export_task["result"]["files"][0]
        cloudconvert.download(url=archivo_salida["url"], local_path=ruta_pdf)
        return ruta_pdf
    else:
        raise Exception("La conversión en CloudConvert falló.")

def generar_carta_cesantias(datos_formulario):
    base_dir = Path(__file__).resolve().parent
    ruta_plantilla = base_dir / "plantillas" / "Carta retiro cesantias.docx"

    nombre_base = f"Carta_Retiro_{datos_formulario.get('cedula', 'temporal')}"
    ruta_docx_salida = str(base_dir / f"{nombre_base}.docx")
    ruta_pdf_salida = str(base_dir / f"{nombre_base}.pdf")

    doc = Document(ruta_plantilla)

    # Aquí se procesan los datos que ingresas en el formulario
    for p in doc.paragraphs:
        if "{{nombre}}" in p.text:
            p.text = p.text.replace("{{nombre}}", datos_formulario.get('nombre', ''))
        if "{{cedula}}" in p.text:
            p.text = p.text.replace("{{cedula}}", datos_formulario.get('cedula', ''))

    doc.save(ruta_docx_salida)

    try:
        convertir_docx_a_pdf_cloudconvert(ruta_docx_salida, ruta_pdf_salida)
        return ruta_docx_salida, ruta_pdf_salida
    except Exception as e:
        print(f"Error: {e}")
        return ruta_docx_salida, None
