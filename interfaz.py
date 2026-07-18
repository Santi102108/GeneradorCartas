import customtkinter as ctk
from pathlib import Path

from generador import generar_carta


class AplicacionCarta(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Generador de cartas")
        self.geometry("700x520")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.frame = ctk.CTkFrame(self)
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.titulo = ctk.CTkLabel(self.frame, text="Generar carta automáticamente", font=ctk.CTkFont(size=24, weight="bold"))
        self.titulo.pack(pady=(20, 20))

        self.campos = {}
        for label, key in [
            ("Nombre", "nombre"),
            ("Cédula", "cedula"),
            ("Valor", "valor"),
            ("Fecha máxima (dd/mm/aa)", "fecha_maxima"),
            ("Fecha expedición (dd/mm/aa)", "fecha_expedicion"),
        ]:
            ctk.CTkLabel(self.frame, text=label, anchor="w").pack(anchor="w", padx=25, pady=(8, 2))
            entry = ctk.CTkEntry(self.frame, placeholder_text=label)
            entry.pack(fill="x", padx=25, pady=(0, 10))
            self.campos[key] = entry

        self.boton = ctk.CTkButton(self.frame, text="Generar", command=self.generar, height=40)
        self.boton.pack(pady=20)

        self.estado = ctk.CTkLabel(self.frame, text="", wraplength=600)
        self.estado.pack(pady=(0, 20))

    def generar(self):
        datos = {
            "nombre": self.campos["nombre"].get().strip(),
            "cedula": self.campos["cedula"].get().strip(),
            "valor": self.campos["valor"].get().strip(),
            "fecha_maxima": self.campos["fecha_maxima"].get().strip(),
            "fecha_expedicion": self.campos["fecha_expedicion"].get().strip(),
        }

        if not datos["nombre"] or not datos["cedula"] or not datos["valor"] or not datos["fecha_maxima"] or not datos["fecha_expedicion"]:
            self.estado.configure(text="Complete todos los campos antes de generar.")
            return

        try:
            carpeta_base = Path(__file__).resolve().parent / "Documentos Generados"
            generar_carta(datos, Path(__file__).resolve().parent / "plantilla.docx", carpeta_base)
            self.estado.configure(text="Carta generada correctamente. Se creó la carpeta del cliente y los archivos Word/PDF.")
        except Exception as exc:
            self.estado.configure(text=f"Error: {exc}")


def main():
    app = AplicacionCarta()
    app.mainloop()
