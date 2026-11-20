"""Pruebas de regresión para montos, formato DOCX y salida PDF."""
import re
import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from docx import Document
from generador import completar_plantilla, generar_pdf, _reemplazar_en_parrafo
from interfaz import app
from utilidades import convertir_numero_a_palabras, normalizar_valor, formatear_fecha_larga

DATOS = {
    "nombre": "Ana María López", "cedula": "123456789",
    "valor": "2.100.000", "fecha_maxima": "17/07/2026",
    "fecha_expedicion": "17/07/2026",
}
CASOS = {
    "480.000": "CUATROCIENTOS OCHENTA MIL PESOS",
    "1.076.000": "UN MILLÓN SETENTA Y SEIS MIL PESOS",
    "2.100.000": "DOS MILLONES CIEN MIL PESOS",
    "7.000.000": "SIETE MILLONES DE PESOS",
    "15.500.000": "QUINCE MILLONES QUINIENTOS MIL PESOS",
}

class ValoresTests(unittest.TestCase):
    def test_montos_requeridos(self):
        for valor, esperado in CASOS.items():
            with self.subTest(valor=valor):
                resultado = convertir_numero_a_palabras(valor)
                self.assertEqual(resultado, esperado)
                self.assertNotIn("PESOS PESOS", resultado)
                self.assertEqual(normalizar_valor("$" + valor), int(valor.replace(".", "")))

    def test_otros_casos_gramaticales(self):
        self.assertEqual(convertir_numero_a_palabras("1.000.000"), "UN MILLÓN DE PESOS")
        self.assertEqual(convertir_numero_a_palabras("100"), "CIEN PESOS")
        self.assertEqual(convertir_numero_a_palabras("21"), "VEINTIÚN PESOS")
        self.assertEqual(formatear_fecha_larga("2026-07-17"), "17 de julio de 2026")

    def test_valores_invalidos(self):
        for valor in ("", "1.23.000", "-500", "100,45", "abc", "0"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    normalizar_valor(valor)

class PlantillaTests(unittest.TestCase):
    def test_reemplazo_dividido_sin_perder_formato(self):
        doc = Document()
        tabla = doc.add_table(rows=1, cols=1)
        celda = tabla.cell(0, 0)
        p = celda.paragraphs[0]
        uno = p.add_run("Valor: {{VALOR_")
        uno.bold = True
        dos = p.add_run("LETRAS}} PESOS")
        dos.italic = True
        _reemplazar_en_parrafo(p, {"{{VALOR_LETRAS}}": CASOS["2.100.000"]})
        self.assertEqual(p.text, "Valor: DOS MILLONES CIEN MIL PESOS")
        self.assertTrue(uno.bold)
        self.assertTrue(dos.italic)
        self.assertEqual(len(doc.tables), 1)

    def test_plantilla_preserva_tablas_y_dimensiones(self):
        with TemporaryDirectory() as temp:
            origen = Path(temp) / "base.docx"
            destino = Path(temp) / "carta.docx"
            doc = Document()
            doc.sections[0].page_width = 7777777
            doc.sections[0].page_height = 9999999
            tabla = doc.add_table(rows=2, cols=2)
            tabla.cell(0,0).text = "{{NOMBRE}}"
            tabla.cell(0,1).text = "{{VALOR_LETRAS}} PESOS"
            tabla.cell(1,0).text = "{{VALOR}}"
            doc.save(origen)
            completar_plantilla(DATOS, destino, origen)
            result = Document(destino)
            self.assertEqual((result.sections[0].page_width, result.sections[0].page_height),
                             (doc.sections[0].page_width, doc.sections[0].page_height))
            self.assertEqual(len(result.tables), len(doc.tables))
            self.assertEqual((len(result.tables[0].rows), len(result.tables[0].columns)), (2,2))
            self.assertEqual(result.tables[0].cell(0,1).text, CASOS["2.100.000"])
            self.assertEqual(result.tables[0].cell(1,0).text, "$2.100.000")

    def test_pdf_bytes_validos_con_conversor_simulado(self):
        with TemporaryDirectory() as temp:
            plantilla = Path(temp) / "plantilla.docx"
            doc = Document()
            doc.add_paragraph("{{NOMBRE}} {{VALOR_LETRAS}}")
            doc.save(plantilla)
            def simulacion(docx, pdf):
                Path(pdf).write_bytes(b"%PDF-1.4" + b"test" * 60)
            with patch("generador.convertir_docx_a_pdf", side_effect=simulacion):
                result = generar_pdf(DATOS, plantilla)
            self.assertTrue(result.startswith(b"%PDF-"))
            self.assertGreater(len(result),100)

class WebTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_formulario(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Generador de cartas", response.data)

    def test_lectura_valor(self):
        response = self.client.post("/api/valor-letras", json={"valor": "2.100.000"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["texto"], CASOS["2.100.000"])

    def test_solo_pdf(self):
        with patch("interfaz.generar_pdf", return_value=b"%PDF-1.4" + b"x" * 160):
            response = self.client.post("/generar", data=DATOS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("attachment", response.headers["Content-Disposition"])
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")

    def test_validacion(self):
        response = self.client.post("/generar", data={**DATOS, "valor": "2.10.000"})
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
