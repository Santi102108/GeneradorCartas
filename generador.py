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
        if clave.upper() == "{{VALOR}}" and not re.search(r"\$\s*$", texto[:inicio]):
            valor = "$" + valor
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
        "{{VALOR}}": datos["valor"],
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


def convertir_docx_a_pdf(ruta_docx, ruta_pdf):
    """Convierte DOCX a PDF localmente, sin cuotas ni servicios externos.

    Cada solicitud dispone de su propio perfil LibreOffice, evitando colisiones.
    """
    import shutil

    comando = os.environ.get("LIBREOFFICE_BIN", "libreoffice")
    if not shutil.which(comando):
        raise RuntimeError("LibreOffice no está disponible en este servidor.")

    ruta_docx = Path(ruta_docx).resolve()
    ruta_pdf = Path(ruta_pdf).resolve()
    ruta_pdf.parent.mkdir(parents=True, exist_ok=True)
    perfil = ruta_docx.parent / "lo_profile"
    try:
        proceso = subprocess.run(
            [
                comando,
                f"-env:UserInstallation={perfil.as_uri()}",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(ruta_pdf.parent),
                str(ruta_docx),
            ],
            check=True, capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("La conversión PDF superó el tiempo permitido.") from exc
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("LibreOffice no pudo convertir la carta a PDF.") from exc

    salida = ruta_pdf.parent / (ruta_docx.stem + ".pdf")
    if salida != ruta_pdf and salida.exists():
        salida.replace(ruta_pdf)
    if not ruta_pdf.is_file() or ruta_pdf.stat().st_size < 100:
        raise RuntimeError(f"LibreOffice no produjo un PDF válido: {proceso.stderr[-300:]}")
    with ruta_pdf.open("rb") as archivo:
        if archivo.read(5) != b"%PDF-":
            raise RuntimeError("El archivo generado no es un PDF válido.")
    return str(ruta_pdf)


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
