from datetime import datetime
import re


def convertir_numero_a_palabras(valor: str) -> str:
    texto = re.sub(r"[^0-9]", "", str(valor))
    if not texto.isdigit():
        raise ValueError("El valor debe contener solo números y puntos.")

    numero = int(texto)
    unidades = [
        "",
        "UN",
        "DOS",
        "TRES",
        "CUATRO",
        "CINCO",
        "SEIS",
        "SIETE",
        "OCHO",
        "NUEVE",
    ]
    decenas = [
        "",
        "",
        "VEINTE",
        "TREINTA",
        "CUARENTA",
        "CINCUENTA",
        "SESENTA",
        "SETENTA",
        "OCHENTA",
        "NOVENTA",
    ]
    centenas = [
        "",
        "CIENTO",
        "DOSCIENTOS",
        "TRESCIENTOS",
        "CUATROCIENTOS",
        "QUINIENTOS",
        "SEISCIENTOS",
        "SETECIENTOS",
        "OCHOCIENTOS",
        "NOVECIENTOS",
    ]

    def convertir_menor_1000(n: int) -> str:
        if n < 10:
            return unidades[n]
        if n < 20:
            if n == 10:
                return "DIEZ"
            if n == 11:
                return "ONCE"
            if n == 12:
                return "DOCE"
            if n == 13:
                return "TRECE"
            if n == 14:
                return "CATORCE"
            if n == 15:
                return "QUINCE"
            if n == 16:
                return "DIECISEIS"
            if n == 17:
                return "DIECISIETE"
            if n == 18:
                return "DIECIOCHO"
            if n == 19:
                return "DIECINUEVE"
        if n < 30:
            if n == 20:
                return "VEINTE"
            return f"VEINTI{unidades[n - 20]}"
        if n < 100:
            resto = n % 10
            if resto == 0:
                return decenas[n // 10]
            return f"{decenas[n // 10]} Y {unidades[resto]}"
        if n < 1000:
            centena = n // 100
            resto = n % 100
            if resto == 0:
                return centenas[centena]
            return f"{centenas[centena]} {convertir_menor_1000(resto)}"
        raise ValueError("Número fuera de rango")

    if numero == 0:
        return "CERO PESOS"

    millones = numero // 1000000
    resto_millones = numero % 1000000
    miles = resto_millones // 1000
    resto = resto_millones % 1000

    partes = []
    if millones:
        if millones == 1:
            partes.append("UN MILLÓN")
        else:
            partes.append(f"{convertir_menor_1000(millones)} MILLONES")
    if miles:
        partes.append(convertir_menor_1000(miles) + " MIL")
    if resto:
        partes.append(convertir_menor_1000(resto))

    texto = " ".join(partes).strip()
    if millones == 1 and miles == 0 and resto == 0:
        return "UN MILLÓN DE PESOS"
    return f"{texto} PESOS".upper().replace("  ", " ")


def formatear_fecha_larga(fecha: str) -> str:
    try:
        fecha_dt = datetime.strptime(fecha, "%d/%m/%y")
    except ValueError:
        raise ValueError("La fecha debe estar en formato dd/mm/aa")

    meses = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]
    return f"{fecha_dt.day} de {meses[fecha_dt.month - 1]} de {fecha_dt.year}"
