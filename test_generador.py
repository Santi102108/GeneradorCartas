import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from generador import generar_carta
from utilidades import convertir_numero_a_palabras, formatear_fecha_larga


class GeneradorTests(unittest.TestCase):
    def test_convertir_numero_a_palabras(self):
        self.assertEqual(
            convertir_numero_a_palabras("1.060.000"),
            "UN MILLÓN SESENTA MIL PESOS",
        )

    def test_convertir_un_millon_a_palabras(self):
        self.assertEqual(
            convertir_numero_a_palabras("1.000.000"),
            "UN MILLÓN DE PESOS",
        )

    def test_formatear_fecha_larga(self):
        self.assertEqual(formatear_fecha_larga("17/07/26"), "17 de julio de 2026")

    def test_generar_carta_crea_documentos(self):
        with TemporaryDirectory() as temp_dir:
            resultado = generar_carta(
                {
                    "nombre": "Juan Pérez",
                    "cedula": "123456789",
                    "valor": "1.060.000",
                    "fecha_maxima": "17/07/26",
                    "fecha_expedicion": "17/07/26",
                },
                Path("plantilla.docx"),
                Path(temp_dir),
            )
            docx_path, pdf_path = resultado
            self.assertTrue(Path(docx_path).exists())
            self.assertTrue(Path(pdf_path).exists())


if __name__ == "__main__":
    unittest.main()
