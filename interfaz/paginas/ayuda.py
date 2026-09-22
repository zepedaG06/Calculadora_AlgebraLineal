import customtkinter as ctk
from interfaz.estilos import PALETA, FUENTE_NORMAL, FUENTE_SECCION


class PaginaAyuda(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=PALETA["fondo"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Ayuda", font=("Segoe UI", 26, "bold"), text_color=PALETA["texto"]).grid(row=0, column=0, sticky="w", padx=28, pady=(24, 12))
        cuerpo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        tarjeta = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        tarjeta.pack(fill="x")
        ctk.CTkLabel(tarjeta, text="Cómo usar la calculadora", font=FUENTE_SECCION, text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(14, 8))
        instrucciones = [
            "Selecciona una sección en el menú lateral.",
            "Configura las dimensiones y llena las entradas con enteros, decimales o fracciones.",
            "Presiona el botón de resolver para ver el resultado.",
            "La calculadora principal también muestra el procedimiento de Gauss-Jordan.",
        ]
        for instruccion in instrucciones:
            ctk.CTkLabel(tarjeta, text=instruccion, font=FUENTE_NORMAL, text_color=PALETA["texto_2"], wraplength=780, justify="left").pack(anchor="w", padx=16, pady=3)
        ctk.CTkLabel(tarjeta, text="").pack(pady=4)
