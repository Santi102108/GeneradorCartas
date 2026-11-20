"""Pruebas de integración con la plantilla real y PDF renderizado.

Se ejecutan en CI con LibreOffice y poppler instalados.
"""
import re
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document
from generador import PLANTILLA, completar_plantilla, convertir_docx_a_pdf
from utilidades import convertir_numero_a_palabras

DATOS_BASE = {
    "nombre": "PRUEBA DE CALIDAD", "cedula": "987654321",
    "fecha_maxima": "2026-12-05", "fecha_expedicion": "2026-11-20",
}
VALORES = ("480.000", "1.076.000", "2.100.000", "7.000.000", "15.500.000")


def parrafos(documento):
    for p in documento.paragraphs:
        yield p
    for tabla in documento.tables:
        for fila in tabla.rows:
            for celda in fila.cells:
                yield from parrafos(celda)


@unittest.skipUnless(shutil.which("libreoffice") and shutil.which("pdftotext")
                     and shutil.which("pdfinfo"), "LibreOffice/Poppler no disponibles")
class PDFIntegracionTests(unittest.TestCase):
    def test_cinco_cartas_pdf_reales_sin_pesos_duplicados(self):
        self.assertTrue(PLANTILLA.is_file(), "La plantilla original debe estar disponible")
        original = Document(PLANTILLA)
        self.assertGreater(len(original.sections), 0)
        fuente = "\n".join(p.text for p in parrafos(original))
        for campo in ("{{NOMBRE}}", "{{CEDULA}}", "{{VALOR}}", "{{VALOR_LETRAS}}"):
            self.assertIn(campo, fuente, f"Falta el marcador {campo} en la plantilla original")
        with TemporaryDirectory() as temp:
            carpeta = Path(temp)
            for numero, valor in enumerate(VALORES):
                with self.subTest(valor=valor):
                    docx = carpeta / f"carta_{numero}.docx"
                    pdf = carpeta / f"carta_{numero}.pdf"
                    datos = {**DATOS_BASE, "valor": valor}
                    completar_plantilla(datos, docx)
                    modificado = Document(docx)
                    self.assertEqual(len(original.tables), len(modificado.tables))
                    self.assertEqual(len(original.sections), len(modificado.sections))
                    for antes, despues in zip(original.sections, modificado.sections):
                        self.assertEqual((antes.page_width, antes.page_height,
                                          antes.left_margin, antes.right_margin),
                                         (despues.page_width, despues.page_height,
                                          despues.left_margin, despues.right_margin))
                    convertir_docx_a_pdf(docx, pdf)
                    self.assertTrue(pdf.read_bytes().startswith(b"%PDF-"))
                    texto = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
                    normalizado = re.sub(r"\s+", " ", texto).upper()
                    self.assertNotIn("PESOS PESOS", normalizado)
                    self.assertIn("PRUEBA DE CALIDAD", normalizado)
                    self.assertIn("987654321", normalizado)
                    esperado = convertir_numero_a_palabras(valor)
                    self.assertIn(esperado, normalizado)
                    self.assertNotIn("{{", texto)
                    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
                    self.assertIn("Pages:", info)
                    self.assertIn("Page size:", info)

if __name__ == "__main__":
    unittest.main()
