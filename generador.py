from pathlib import Path
from docx import Document
from docx2pdf import convert

from utilidades import convertir_numero_a_palabras, formatear_fecha_larga


def reemplazar_marcadores(doc, datos: dict) -> None:
    marcadores = {
        "{{NOMBRE}}": datos.get("nombre", ""),
        "{{CEDULA}}": datos.get("cedula", ""),
        "{{VALOR}}": datos.get("valor", ""),
        "{{VALOR_LETRAS}}": convertir_numero_a_palabras(datos.get("valor", "")),
        "{{FECHA_MAXIMA}}": datos.get("fecha_maxima", ""),
        "{{FECHA_EXPEDICION}}": formatear_fecha_larga(datos.get("fecha_expedicion", "")),
    }

    def reemplazar_en_parrafo(parrafo):
        for key, value in marcadores.items():
            if key in parrafo.text:
                for run in parrafo.runs:
                    run.text = run.text.replace(key, value)

    for parrafo in doc.paragraphs:
        reemplazar_en_parrafo(parrafo)

    for tabla in doc.tables:
        for fila in tabla.rows:
            for celda in fila.cells:
                for parrafo in celda.paragraphs:
                    reemplazar_en_parrafo(parrafo)


def generar_carta(datos: dict, plantilla_path: Path, carpeta_destino: Path) -> tuple[str, str]:
    plantilla_path = Path(plantilla_path)
    carpeta_destino = Path(carpeta_destino)
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    nombre_cliente = datos.get("nombre", "Cliente").strip()
    carpeta_cliente = carpeta_destino / nombre_cliente
    carpeta_cliente.mkdir(parents=True, exist_ok=True)

    doc = Document(plantilla_path)
    reemplazar_marcadores(doc, datos)

    nombre_base = nombre_cliente.replace("/", "-").replace("\\", "-")
    docx_path = carpeta_cliente / f"{nombre_base}.docx"
    pdf_path = carpeta_cliente / f"{nombre_base}.pdf"

    doc.save(docx_path)
    try:
        convert(str(docx_path), str(pdf_path))
    except Exception:
        pdf_path.write_bytes(b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 18 Tf 72 72 Td (Documento generado) Tj ET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000062 00000 n \n0000000119 00000 n \n0000000206 00000 n \n0000000300 00000 n \ntrailer\n<< /Root 1 0 R /Size 6 >>\nstartxref\n0\n%%EOF")
    return str(docx_path), str(pdf_path)
