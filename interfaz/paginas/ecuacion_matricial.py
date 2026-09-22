import customtkinter as ctk
from tkinter import messagebox

from logica.ecuacion_matricial import resolver_ecuacion_matricial
from interfaz.componentes import EntradaMatriz, PanelResultado
from interfaz.estilos import PALETA, FUENTE_SECCION


class PaginaEcuacionMatricial(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=PALETA["fondo"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Ecuación Matricial Ax = b", font=("Segoe UI", 26, "bold"), text_color=PALETA["texto"]).grid(row=0, column=0, sticky="w", padx=28, pady=(24, 12))
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_rowconfigure(1, weight=1)
        config = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        config.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        ctk.CTkLabel(config, text="Configuración de Ax = b", font=FUENTE_SECCION).pack(anchor="w", padx=16, pady=(12, 8))
        fila = ctk.CTkFrame(config, fg_color="transparent")
        fila.pack(anchor="w", padx=16, pady=(0, 12))
        ctk.CTkLabel(fila, text="Filas").pack(side="left", padx=(0, 8))
        self.filas = ctk.CTkEntry(fila, width=70, justify="center")
        self.filas.insert(0, "3")
        self.filas.pack(side="left", padx=(0, 14))
        ctk.CTkLabel(fila, text="Columnas").pack(side="left", padx=(0, 8))
        self.columnas = ctk.CTkEntry(fila, width=70, justify="center")
        self.columnas.insert(0, "3")
        self.columnas.pack(side="left", padx=(0, 14))
        ctk.CTkButton(fila, text="Crear matriz", fg_color=PALETA["primario"], hover_color=PALETA["primario_hover"], text_color="#04191A", command=self.crear_matriz).pack(side="left")
        self.entrada = EntradaMatriz(cuerpo, self.resolver, titulo="Matriz A y vector b")
        self.entrada.grid(row=1, column=0, sticky="nsew")
        self.resultado = PanelResultado(cuerpo)
        self.resultado.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        self.crear_matriz()

    def crear_matriz(self):
        try:
            m, n = int(self.filas.get()), int(self.columnas.get())
            if not 1 <= m <= 10 or not 1 <= n <= 10:
                raise ValueError
            self.entrada.crear(m, n)
            self.resultado.placeholder()
        except ValueError:
            messagebox.showerror("Entrada invalida", "Las filas y columnas deben estar entre 1 y 10.")

    def resolver(self):
        try:
            A, b = self.entrada.leer()
            self.resultado.mostrar(resolver_ecuacion_matricial(A, b))
        except Exception as error:
            messagebox.showerror("Error", str(error))
