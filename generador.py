"""Motor de generación conservando la plantilla DOCX original.

DOCX es un artefacto temporal interno; la salida pública es siempre PDF.
"""
import os
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document
from utilidades import convertir_numero_a_palabras, normalizar_valor

BASE_DIR = Path(__file__).resolve().parent
PLANTILLA = BASE_DIR / "plantilla.docx"
CAMPOS = ("nombre", "cedula", "valor", "fecha_maxima", "fecha_expedicion")


def validar_datos(datos):
    if not isinstance(datos, dict):
        raise ValueError("Datos de la carta inválidos.")
    limpio = {campo: str(datos.get(campo, "")).strip() for campo in CAMPOS}
    faltantes = [campo.replace("_", " ") for campo, valor in limpio.items() if not valor]
    if faltantes:
        raise ValueError("Faltan campos obligatorios: " + ", ".join(faltantes))
    for campo in ("nombre", "cedula"):
        if len(limpio[campo]) > 150:
            raise ValueError(f"El campo {campo} es demasiado largo.")
    if not re.fullmatch(r"[0-9.\- ]{5,25}", limpio["cedula"]):
        raise ValueError("La cédula debe contener cifras válidas.")
    importe = normalizar_valor(limpio["valor"])
    limpio["valor"] = f"{importe:,}".replace(",", ".")
    from datetime import datetime
    for campo in ("fecha_maxima", "fecha_expedicion"):
        fecha = limpio[campo]
        for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
            try:
                parsed = datetime.strptime(fecha, formato)
                limpio[campo] = parsed.strftime("%d/%m/%Y")
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Fecha inválida en {campo.replace('_', ' ')}.")
    return limpio


def _reemplazar_en_parrafo(parrafo, reemplazos):
    """Edita únicamente texto de runs y conserva sus propiedades, tablas y bordes."""
    runs = parrafo.runs
    if not runs:
        return
    texto = "".join(run.text for run in runs)
    if "{{" not in texto:
        return
    # Eliminar PESOS redundante solo junto al marcador monetario.
    patrones = [r"{{VALOR_LETRAS}}(?:[ \t]+PESOS)?"] if "{{VALOR_LETRAS}}" in reemplazos else []
    patrones.extend(re.escape(x) for x in reemplazos if x != "{{VALOR_LETRAS}}")
    if not patrones:
        return
    patron = re.compile("|".join(patrones), re.IGNORECASE)
    coincidencias = list(patron.finditer(texto))
    for coincidencia in reversed(coincidencias):
        clave = coincidencia.group(0)
        valor = (reemplazos["{{VALOR_LETRAS}}"]
                 if clave.upper().startswith("{{VALOR_LETRAS}}")
                 else reemplazos.get(clave.upper(), clave))
        inicio, fin = coincidencia.span()
        posiciones = []
        for i, run in enumerate(runs):
            for j in range(len(run.text)):
                posiciones.append((i, j))
        if fin > len(posiciones):
            continue
        i_inicio, j_inicio = posiciones[inicio]
        i_fin, j_fin = posiciones[fin - 1]
        if i_inicio == i_fin:
            original = runs[i_inicio].text
            runs[i_inicio].text = original[:j_inicio] + valor + original[j_fin + 1:]
        else:
            runs[i_inicio].text = runs[i_inicio].text[:j_inicio] + valor
            for k in range(i_inicio + 1, i_fin):
                runs[k].text = ""
            runs[i_fin].text = runs[i_fin].text[j_fin + 1:]


def _todos_los_parrafos(contenedor):
    for parrafo in contenedor.paragraphs:
        yield parrafo
    for tabla in contenedor.tables:
        for fila in tabla.rows:
            for celda in fila.cells:
                yield from _todos_los_parrafos(celda)


def completar_plantilla(datos, salida_docx, plantilla=PLANTILLA):
    datos = validar_datos(datos)
    if not Path(plantilla).is_file():
        raise FileNotFoundError("No se encontró la plantilla original.")
    doc = Document(str(plantilla))
    reemplazos = {
        "{{NOMBRE}}": datos["nombre"],
        "{{CEDULA}}": datos["cedula"],
        "{{VALOR}}": "$" + datos["valor"],
        "{{VALOR_LETRAS}}": convertir_numero_a_palabras(datos["valor"]),
        "{{FECHA_MAXIMA}}": datos["fecha_maxima"],
        "{{FECHA_EXPEDICION}}": datos["fecha_expedicion"],
    }
    contenedores = [doc]
    for seccion in doc.sections:
        contenedores.extend((seccion.header, seccion.footer))
    for contenedor in contenedores:
        for parrafo in _todos_los_parrafos(contenedor):
            _reemplazar_en_parrafo(parrafo, reemplazos)
    texto = "\n".join(p.text for c in contenedores for p in _todos_los_parrafos(c))
    for marcador in reemplazos:
        if marcador in texto:
            raise ValueError(f"La plantilla contiene un campo pendiente: {marcador}")
    doc.save(str(salida_docx))
    return str(salida_docx)


def convertir_docx_a_pdf_cloudconvert(ruta_docx, ruta_pdf):
    """CloudConvert preserva el flujo basado en DOCX del proyecto original."""
    clave = os.environ.get("CLOUDCONVERT_API_KEY", "").strip()
    if not clave:
        raise RuntimeError("No se configuró CLOUDCONVERT_API_KEY para exportar el PDF.")
    import cloudconvert
    cloudconvert.configure(api_key=clave)
    trabajo = cloudconvert.Job.create(payload={"tasks": {
        "importar": {"operation": "import/upload"},
        "convertir": {"operation": "convert", "input": "importar",
                      "output_format": "pdf", "engine": "office"},
        "exportar": {"operation": "export/url", "input": "convertir"}}})
    carga = next(t for t in trabajo["tasks"] if t["operation"] == "import/upload")
    cloudconvert.Task.upload(file_name=str(ruta_docx), task=carga)
    terminado = cloudconvert.Job.wait(id=trabajo["id"])
    tarea = next(t for t in terminado["tasks"] if t["operation"] == "export/url")
    if tarea.get("status") != "finished" or not tarea.get("result", {}).get("files"):
        raise RuntimeError("CloudConvert no produjo un PDF válido.")
    cloudconvert.download(url=tarea["result"]["files"][0]["url"], filename=str(ruta_pdf))


def convertir_docx_a_pdf(ruta_docx, ruta_pdf):
    if os.environ.get("CLOUDCONVERT_API_KEY", "").strip():
        convertir_docx_a_pdf_cloudconvert(ruta_docx, ruta_pdf)
    else:
        # LibreOffice es una alternativa local; no se envían datos a terceros.
        comando = os.environ.get("LIBREOFFICE_BIN", "libreoffice")
        try:
            subprocess.run([comando, f"-env:UserInstallation={Path(ruta_docx).parent.joinpath('lo_profile').as_uri()}",
                            "--headless", "--convert-to", "pdf", "--outdir",
                            str(Path(ruta_pdf).parent), str(ruta_docx)],
                           check=True, capture_output=True, timeout=90)
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError(
                "No se pudo producir el PDF. Configure CLOUDCONVERT_API_KEY "
                "o instale LibreOffice en el servidor.") from exc
    destino = Path(ruta_pdf)
    if not destino.is_file() or destino.stat().st_size < 100 or destino.read_bytes()[:5] != b"%PDF-":
        raise RuntimeError("El archivo producido no es un PDF válido.")
    return str(destino)


def generar_pdf(datos, plantilla=PLANTILLA):
    """Devuelve bytes PDF, sin dejar archivos personales persistentes."""
    with TemporaryDirectory(prefix="cartas_") as tmp:
        docx = Path(tmp) / "carta.docx"
        pdf = Path(tmp) / "carta.pdf"
        completar_plantilla(datos, docx, plantilla)
        convertir_docx_a_pdf(docx, pdf)
        return pdf.read_bytes()


def generar_carta_cesantias(datos_formulario):
    """Compatibilidad con integraciones previas; preferir generar_pdf."""
    with TemporaryDirectory(prefix="cartas_") as tmp:
        docx = Path(tmp) / "carta.docx"
        completar_plantilla(datos_formulario, docx)
        pdf = Path(tmp) / "carta.pdf"
        convertir_docx_a_pdf(docx, pdf)
        return None, pdf.read_bytes()
