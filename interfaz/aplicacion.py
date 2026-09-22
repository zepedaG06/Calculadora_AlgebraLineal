import os
import tkinter as tk
import customtkinter as ctk

from .estilos import PALETA, FUENTE_PEQUENA, resolver_color, configurar_customtkinter
from .paginas.calculadora import PaginaCalculadora
from .paginas.combinacion_lineal import PaginaCombinacionLineal
from .paginas.ecuacion_matricial import PaginaEcuacionMatricial
from .paginas.independencia_lineal import PaginaIndependenciaLineal
from .paginas.metodo_eliminacion import PaginaMetodoEliminacion
from .paginas.operaciones_elementales import PaginaOperacionesElementales
from .paginas.ayuda import PaginaAyuda


class AplicacionAlgebraLineal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora de Algebra Lineal - Grupo 3 - UAM")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(fg_color=PALETA["fondo"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.crear_sidebar()
        self.crear_paginas()

    def crear_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=PALETA["sidebar"], corner_radius=0, width=240)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        ctk.CTkLabel(sidebar, text="Algebra\nLineal", font=("Segoe UI", 19, "bold"), justify="left", text_color=PALETA["texto"]).pack(anchor="w", padx=24, pady=(28, 8))
        ctk.CTkLabel(sidebar, text="Universidad Americana • Grupo 3", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"]).pack(anchor="w", padx=24, pady=(0, 18))
        ctk.CTkFrame(sidebar, height=1, fg_color=PALETA["borde"]).pack(fill="x", padx=24, pady=(0, 14))
        self.nav_botones = {}
        opciones = [
            ("calculadora", "Calculadora"),
            ("elementales", "Operaciones Elementales"),
            ("vectorial", "Combinaciones Lineales"),
            ("axb", "Ecuación Matricial Ax=b"),
            ("independencia", "Independencia Lineal"),
            ("metodo", "Método de Eliminación"),
            ("ayuda", "Ayuda"),
        ]
        for clave, texto in opciones:
            self.nav_botones[clave] = ctk.CTkButton(sidebar, text=texto, anchor="w", height=38, corner_radius=8, fg_color="transparent", hover_color=PALETA["secundario_hover"], text_color=PALETA["texto"], command=lambda pagina=clave: self.cambiar_pagina(pagina))
            self.nav_botones[clave].pack(fill="x", padx=16, pady=4)
        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkLabel(sidebar, text="Excellentia\nAcademica", font=("Segoe UI", 10), text_color=PALETA["texto_3"], justify="left").pack(anchor="w", padx=24, pady=20)

    def crear_paginas(self):
        contenedor = ctk.CTkFrame(self, fg_color=PALETA["fondo"], corner_radius=0)
        contenedor.grid(row=0, column=1, sticky="nsew")
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.paginas = {
            "calculadora": PaginaCalculadora(contenedor),
            "vectorial": PaginaCombinacionLineal(contenedor),
            "elementales": PaginaOperacionesElementales(contenedor),
            "axb": PaginaEcuacionMatricial(contenedor),
            "independencia": PaginaIndependenciaLineal(contenedor),
            "metodo": PaginaMetodoEliminacion(contenedor),
            "ayuda": PaginaAyuda(contenedor),
        }
        for pagina in self.paginas.values():
            pagina.grid(row=0, column=0, sticky="nsew")
        self.cambiar_pagina("calculadora")

    def cambiar_pagina(self, pagina):
        for nombre, boton in self.nav_botones.items():
            activo = nombre == pagina
            boton.configure(fg_color=PALETA["primario"] if activo else "transparent", text_color="#04191A" if activo else PALETA["texto"])
        self.paginas[pagina].tkraise()


def iniciar():
    configurar_customtkinter(ctk)
    app = AplicacionAlgebraLineal()
    app.mainloop()
