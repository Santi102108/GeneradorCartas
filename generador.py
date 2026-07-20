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
        raise ValueError("La variable CLOUDCONVERT_API_KEY no está configurada en Render.")

    # Creamos el trabajo de conversión
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

    # Buscamos la tarea de subida correctamente usando filtros del SDK
    upload_task = filter(lambda task: task['operation'] == 'import/upload', job['tasks'])
    upload_task = list(upload_task)[0]

    # Subimos el archivo local de Word
    cloudconvert.Task.upload(file_name=ruta_docx, task=upload_task)
    
    # Esperamos a que todo el proceso termine
    completed_job = cloudconvert.Job.wait(id=job["id"])

    # Buscamos la tarea de exportación finalizada
    export_task = filter(lambda task: task['operation'] == 'export/url', completed_job['tasks'])
    export_task = list(export_task)[0]

    if export_task["status"] == "finished" and export_task["result"]["files"]:
        archivo_salida = export_task["result"]["files"][0]
        # Descargamos el archivo PDF generado
        cloudconvert.download(url=archivo_salida["url"], local_path=ruta_pdf)
        return ruta_pdf
    else:
        raise Exception("La conversión en CloudConvert falló en los servidores externos.")

def generar_carta_cesantias(datos_formulario):
    base_dir = Path(__file__).resolve().parent
    ruta_plantilla = base_dir / "plantilla.docx"

    nombre_base = f"Carta_Retiro_{datos_formulario.get('cedula', 'temporal')}"
    ruta_docx_salida = str(base_dir / f"{nombre_base}.docx")
    ruta_pdf_salida = str(base_dir / f"{nombre_base}.pdf")

    doc = Document(ruta_plantilla)

    # Reemplazo de marcadores en el Word
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
        print(f"Error convirtiendo a PDF: {e}")
        # Si falla por API o credenciales, devuelve el Word para no romper la app
        return ruta_docx_salida, None
