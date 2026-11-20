"""Normalización de importes colombianos y fechas."""
from datetime import datetime
import re
from num2words import num2words


def normalizar_valor(valor):
    """Convierte un importe COP sin centavos a un entero, sin redondeos silenciosos."""
    if isinstance(valor, bool):
        raise ValueError("El valor debe ser numérico.")
    texto = str(valor).strip().upper()
    texto = re.sub(r"^(?:COP\\s*)?\\$?\\s*", "", texto)
    texto = re.sub(r"\\s*(?:COP|M/CTE|PESOS)\\s*$", "", texto).strip()
    texto = texto.replace(" ", "")
    if re.fullmatch(r"\\d{1,3}(?:\\.\\d{3})+(?:,00)?", texto):
        texto = texto.split(",")[0].replace(".", "")
    elif re.fullmatch(r"\\d+(?:,00)?", texto):
        texto = texto.split(",")[0]
    else:
        raise ValueError("Valor inválido. Ejemplo: 2.100.000 (sin centavos).")
    numero = int(texto)
    if not 0 < numero <= 999_999_999_999:
        raise ValueError("El valor debe ser mayor que cero y menor a un billón.")
    return numero


def convertir_numero_a_palabras(valor):
    """Devuelve una única denominación PESOS, incluso en millones exactos."""
    numero = normalizar_valor(valor)
    texto = num2words(numero, lang="es").upper()
    # Ante el sustantivo masculino PESOS, uno se apocopa.
    texto = re.sub(r"VEINTIUNO$", "VEINTIÚN", texto)
    texto = re.sub(r"\\bUNO$", "UN", texto)
    if numero % 1_000_000 == 0:
        return f"{texto} DE PESOS"
    return f"{texto} PESOS"


def formatear_fecha_larga(fecha):
    texto = str(fecha).strip()
    formatos = ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d")
    for formato in formatos:
        try:
            fecha_dt = datetime.strptime(texto, formato)
            break
        except ValueError:
            continue
    else:
        raise ValueError("Fecha inválida: utiliza dd/mm/aaaa o aaaa-mm-dd.")
    meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
    return f"{fecha_dt.day} de {meses[fecha_dt.month - 1]} de {fecha_dt.year}"
