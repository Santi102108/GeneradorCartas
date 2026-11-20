"""Garantiza que el motor PDF local no usa CloudConvert."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from generador import convertir_docx_a_pdf


class ConversionLocalTests(unittest.TestCase):
    def test_pdf_local_incluso_si_existe_clave_antigua(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            origen = base / "carta.docx"
            salida = base / "carta.pdf"
            origen.write_bytes(b"test docx")
            comandos = []

            def ejecutar(cmd, **kwargs):
                comandos.append(cmd)
                salida.write_bytes(b"%PDF-1.4" + b"x" * 200)
                return SimpleNamespace(stderr="", stdout="")

            with patch.dict(os.environ, {"CLOUDCONVERT_API_KEY": "clave-antigua-no-usar"}), \
                 patch("shutil.which", return_value="/usr/bin/libreoffice"), \
                 patch("subprocess.run", side_effect=ejecutar):
                self.assertEqual(convertir_docx_a_pdf(origen, salida), str(salida))
            self.assertEqual(len(comandos), 1)
            self.assertEqual(comandos[0][0], "libreoffice")
            self.assertIn("--headless", comandos[0])
            self.assertIn("--convert-to", comandos[0])

    def test_sin_libreoffice_falla_claramente(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            with patch("shutil.which", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "LibreOffice"):
                    convertir_docx_a_pdf(p / "a.docx", p / "a.pdf")


if __name__ == "__main__":
    unittest.main()
