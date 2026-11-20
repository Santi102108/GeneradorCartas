"""Prueba end-to-end del contenedor con cinco PDFs reales."""
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:10000"
CASOS = {
    "480.000": "CUATROCIENTOS OCHENTA MIL PESOS",
    "1.076.000": "UN MILLÓN SETENTA Y SEIS MIL PESOS",
    "2.100.000": "DOS MILLONES CIEN MIL PESOS",
    "7.000.000": "SIETE MILLONES DE PESOS",
    "15.500.000": "QUINCE MILLONES QUINIENTOS MIL PESOS",
}


def main():
    for _ in range(45):
        try:
            with urlopen(BASE + "/health", timeout=3) as respuesta:
                if json.load(respuesta).get("status") == "ok":
                    break
        except Exception:
            time.sleep(2)
    else:
        raise RuntimeError("El servicio Docker no respondió.")

    with tempfile.TemporaryDirectory() as temporal:
        for i, (importe, letras) in enumerate(CASOS.items()):
            datos = urlencode({
                "nombre": "PRUEBA DE CALIDAD",
                "cedula": "987654321",
                "valor": importe,
                "fecha_maxima": "2026-12-05",
                "fecha_expedicion": "2026-11-20",
            }).encode()
            solicitud = Request(BASE + "/generar", data=datos, method="POST")
            with urlopen(solicitud, timeout=150) as respuesta:
                assert respuesta.headers.get_content_type() == "application/pdf"
                pdf = respuesta.read()
            assert pdf.startswith(b"%PDF-") and len(pdf) > 100
            ruta = Path(temporal) / f"carta_{i}.pdf"
            ruta.write_bytes(pdf)
            texto = subprocess.check_output(["pdftotext", "-layout", str(ruta), "-"], text=True)
            texto = re.sub(r"\s+", " ", texto).upper()
            assert letras in texto, (importe, texto[:1000])
            assert "PESOS PESOS" not in texto
            assert "PRUEBA DE CALIDAD" in texto
            info = subprocess.check_output(["pdfinfo", str(ruta)], text=True)
            assert "Pages:" in info and "Page size:" in info
            print("OK PDF local:", importe)
    print("ÉXITO: cinco PDF reales, sin conversor externo.")


if __name__ == "__main__":
    main()
