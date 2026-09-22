import customtkinter as ctk
from tkinter import messagebox

from logica.nucleo.formato import convertir_numero, formatear_numero
from logica.independencia_lineal import analizar_independencia
from interfaz.estilos import PALETA, FUENTE_SECCION, FUENTE_NORMAL, FUENTE_MONO


class PaginaIndependenciaLineal(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=PALETA["fondo"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Independencia Lineal", font=("Segoe UI", 26, "bold"), text_color=PALETA["texto"]).grid(row=0, column=0, sticky="w", padx=28, pady=(24, 12))
        cuerpo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        config = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        config.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(config, text="Configuración", font=FUENTE_SECCION).pack(anchor="w", padx=16, pady=(12, 8))
        fila = ctk.CTkFrame(config, fg_color="transparent")
        fila.pack(anchor="w", padx=16, pady=(0, 12))
        ctk.CTkLabel(fila, text="Dimensión").pack(side="left", padx=(0, 8))
        self.dimension = ctk.CTkEntry(fila, width=70, justify="center")
        self.dimension.insert(0, "3")
        self.dimension.pack(side="left", padx=(0, 14))
        ctk.CTkLabel(fila, text="Vectores").pack(side="left", padx=(0, 8))
        self.cantidad = ctk.CTkEntry(fila, width=70, justify="center")
        self.cantidad.insert(0, "3")
        self.cantidad.pack(side="left", padx=(0, 14))
        ctk.CTkButton(fila, text="Crear vectores", fg_color=PALETA["primario"], hover_color=PALETA["primario_hover"], text_color="#04191A", command=self.crear).pack(side="left")
        self.entrada = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        self.entrada.pack(fill="x", pady=(0, 14))
        self.resultado = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        self.resultado.pack(fill="x")
        self.crear()

    def crear(self):
        try:
            dimension, cantidad = int(self.dimension.get()), int(self.cantidad.get())
            if not 1 <= dimension <= 10 or not 1 <= cantidad <= 10:
                raise ValueError
        except ValueError:
            messagebox.showerror("Entrada invalida", "Las dimensiones deben estar entre 1 y 10.")
            return
        for widget in self.entrada.winfo_children():
            widget.destroy()
        self.entradas = []
        tabla = ctk.CTkFrame(self.entrada, fg_color=PALETA["panel_2"])
        tabla.pack(fill="x", padx=16, pady=16)
        for j in range(cantidad):
            ctk.CTkLabel(tabla, text=f"v{j + 1}", text_color=PALETA["primario"]).grid(row=0, column=j, padx=6, pady=8)
        for i in range(dimension):
            fila = []
            for j in range(cantidad):
                entrada = ctk.CTkEntry(tabla, width=78, justify="center")
                entrada.insert(0, "0")
                entrada.grid(row=i + 1, column=j, padx=5, pady=4)
                fila.append(entrada)
            self.entradas.append(fila)
        ctk.CTkButton(self.entrada, text="Analizar independencia", fg_color=PALETA["primario"], hover_color=PALETA["primario_hover"], text_color="#04191A", command=self.resolver).pack(anchor="w", padx=16, pady=(0, 16))
        self.mostrar_resultado(None)

    def resolver(self):
        try:
            A = [[convertir_numero(celda.get()) for celda in fila] for fila in self.entradas]
            self.mostrar_resultado(analizar_independencia(A))
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def mostrar_resultado(self, resultado):
        for widget in self.resultado.winfo_children():
            widget.destroy()
        if resultado is None:
            ctk.CTkLabel(self.resultado, text="El resultado aparecerá aquí.", text_color=PALETA["texto_3"]).pack(anchor="w", padx=16, pady=18)
            return
        independiente = resultado["independiente"]
        titulo = "Los vectores son linealmente independientes." if independiente else "Los vectores son linealmente dependientes."
        ctk.CTkLabel(self.resultado, text=titulo, font=FUENTE_SECCION, text_color=PALETA["exito"] if independiente else PALETA["advertencia"]).pack(anchor="w", padx=16, pady=(14, 6))
        if resultado.get("solucion") is not None:
            texto = ", ".join(f"c{i + 1} = {formatear_numero(v)}" for i, v in enumerate(resultado["solucion"]))
            ctk.CTkLabel(self.resultado, text=texto, font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=(0, 14))
        elif resultado.get("expresiones"):
            for indice, expresion in resultado["expresiones"].items():
                ctk.CTkLabel(self.resultado, text=f"c{indice + 1} = {expresion}", font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
