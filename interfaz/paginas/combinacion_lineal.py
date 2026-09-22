import customtkinter as ctk
from tkinter import messagebox

from logica.combinaciones_lineales import resolver_combinacion_lineal
from logica.nucleo.formato import convertir_numero, formatear_numero, matriz_a_texto
from interfaz.estilos import PALETA, FUENTE_SECCION, FUENTE_NORMAL, FUENTE_MONO
from interfaz.componentes import PanelProcedimiento


class PaginaCombinacionLineal(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=PALETA["fondo"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Combinaciones Lineales", font=("Segoe UI", 26, "bold"), text_color=PALETA["texto"]).grid(row=0, column=0, sticky="w", padx=28, pady=(24, 12))
        cuerpo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        config = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        config.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(config, text="c1·v1 + c2·v2 + ... + cn·vn = w", font=FUENTE_SECCION, text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 8))
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
        ctk.CTkButton(fila, text="Crear combinación", fg_color=PALETA["primario"], hover_color=PALETA["primario_hover"], text_color="#04191A", command=self.crear).pack(side="left")
        self.entrada = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        self.entrada.pack(fill="x", pady=(0, 14))
        self.procedimiento = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        self.procedimiento.pack(fill="both", expand=True, pady=(0, 14))
        ctk.CTkLabel(
            self.procedimiento,
            text="Procedimiento de Gauss-Jordan",
            font=FUENTE_SECCION,
        ).pack(anchor="w", padx=16, pady=(14, 8))
        self.panel_procedimiento = PanelProcedimiento(self.procedimiento)
        self.panel_procedimiento.pack(fill="both", expand=True, padx=8, pady=(0, 12))
        self.resultado = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        self.resultado.pack(fill="x")
        self.crear()

    def crear(self):
        try:
            dimension, cantidad = int(self.dimension.get()), int(self.cantidad.get())
            if not 1 <= dimension <= 10 or not 2 <= cantidad <= 10:
                raise ValueError
        except ValueError:
            messagebox.showerror("Entrada invalida", "La dimensión debe estar entre 1 y 10 y los vectores entre 2 y 10.")
            return
        for widget in self.entrada.winfo_children():
            widget.destroy()
        self.entradas = []
        tabla = ctk.CTkFrame(self.entrada, fg_color=PALETA["panel_2"])
        tabla.pack(fill="x", padx=16, pady=16)
        for j, texto in enumerate(["Componente"] + [f"v{i + 1}" for i in range(cantidad)] + ["w"]):
            ctk.CTkLabel(tabla, text=texto, text_color=PALETA["primario"]).grid(row=0, column=j, padx=6, pady=8)
        for i in range(dimension):
            ctk.CTkLabel(tabla, text=str(i + 1)).grid(row=i + 1, column=0, padx=6, pady=4)
            fila = []
            for j in range(cantidad + 1):
                entrada = ctk.CTkEntry(tabla, width=78, justify="center")
                entrada.insert(0, "0")
                entrada.grid(row=i + 1, column=j + 1, padx=5, pady=4)
                fila.append(entrada)
            self.entradas.append(fila)
        ctk.CTkButton(self.entrada, text="Resolver combinación lineal", fg_color=PALETA["primario"], hover_color=PALETA["primario_hover"], text_color="#04191A", command=self.resolver).pack(anchor="w", padx=16, pady=(0, 16))
        self.panel_procedimiento.placeholder()
        self.mostrar_resultado(None)

    def resolver(self):
        try:
            cantidad = len(self.entradas[0]) - 1
            filas = [[convertir_numero(celda.get()) for celda in fila] for fila in self.entradas]
            vectores = [[fila[indice] for fila in filas] for indice in range(cantidad)]
            objetivo = [fila[-1] for fila in filas]
            resultado = resolver_combinacion_lineal(vectores, objetivo)
            self.panel_procedimiento.mostrar(resultado["pasos"])
            self.mostrar_resultado(resultado)
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def mostrar_resultado(self, resultado):
        for widget in self.resultado.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.resultado, text="Resultado", font=FUENTE_SECCION).pack(anchor="w", padx=16, pady=(14, 8))
        if resultado is None:
            ctk.CTkLabel(self.resultado, text="Ingresa los vectores y resuelve la combinación.", text_color=PALETA["texto_3"]).pack(anchor="w", padx=16, pady=(0, 16))
            return
        ctk.CTkLabel(
            self.resultado,
            text="Sistema construido: A·c = w",
            font=("Segoe UI", 13, "bold"),
            text_color=PALETA["primario"],
        ).pack(anchor="w", padx=16, pady=(0, 4))
        ctk.CTkLabel(
            self.resultado,
            text=(
                "Los vectores ingresados forman las columnas de A y el vector w "
                "es la última columna de la matriz aumentada:"
            ),
            font=FUENTE_NORMAL,
            text_color=PALETA["texto_2"],
            wraplength=760,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 6))
        ctk.CTkLabel(
            self.resultado,
            text=matriz_a_texto(resultado["matriz_inicial"]),
            font=FUENTE_MONO,
            text_color=PALETA["texto_2"],
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))
        ctk.CTkLabel(self.resultado, text=resultado["clasificacion"], font=FUENTE_NORMAL, text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=4)
        if resultado.get("solucion") is not None:
            texto = ", ".join(f"c{i + 1} = {formatear_numero(valor)}" for i, valor in enumerate(resultado["solucion"]))
            ctk.CTkLabel(self.resultado, text=texto, font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=(0, 14))
        elif resultado.get("expresiones") is not None:
            for indice, expresion in resultado["expresiones"].items():
                ctk.CTkLabel(self.resultado, text=f"c{indice + 1} = {expresion}", font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)


