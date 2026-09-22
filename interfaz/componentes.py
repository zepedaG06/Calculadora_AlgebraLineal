import tkinter as tk
import customtkinter as ctk

from logica.nucleo.formato import convertir_numero, formatear_numero, matriz_a_texto
from .estilos import PALETA, FUENTE_MONO, FUENTE_NORMAL, FUENTE_PEQUENA, FUENTE_SECCION, resolver_color


class EntradaMatriz(ctk.CTkFrame):
    def __init__(self, parent, al_resolver, al_limpiar=None, titulo="Matriz aumentada [A | b]"):
        super().__init__(parent, fg_color=PALETA["panel"], corner_radius=12, border_width=1, border_color=PALETA["borde"])
        self.al_resolver = al_resolver
        self.al_limpiar = al_limpiar
        self.entradas = []
        self.m = self.n = 0
        ctk.CTkLabel(self, text=titulo, font=FUENTE_SECCION).pack(anchor="w", padx=18, pady=(16, 8))
        self.dimension = ctk.CTkLabel(self, text="", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"])
        self.dimension.pack(anchor="w", padx=18, pady=(0, 8))
        self.tabla = ctk.CTkFrame(self, fg_color=PALETA["panel_2"], corner_radius=10)
        self.tabla.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        acciones = ctk.CTkFrame(self, fg_color="transparent")
        acciones.pack(anchor="w", padx=18, pady=(0, 16))
        ctk.CTkButton(acciones, text="Resolver sistema", height=40, fg_color=PALETA["primario"], hover_color=PALETA["primario_hover"], text_color="#04191A", command=self.al_resolver).pack(side="left")
        if al_limpiar:
            ctk.CTkButton(acciones, text="Limpiar", height=40, fg_color=PALETA["secundario"], hover_color=PALETA["secundario_hover"], command=al_limpiar).pack(side="left", padx=10)

    def crear(self, m, n):
        for widget in self.tabla.winfo_children():
            widget.destroy()
        self.m, self.n = m, n
        self.entradas = []
        self.dimension.configure(text=f"{m} ecuaciones x {n} variables")
        for j in range(n):
            ctk.CTkLabel(self.tabla, text=f"x{j + 1}", text_color=PALETA["primario"]).grid(row=0, column=j, padx=5, pady=8)
        ctk.CTkLabel(self.tabla, text="b", text_color=PALETA["primario"]).grid(row=0, column=n, padx=5, pady=8)
        for i in range(m):
            fila = []
            for j in range(n + 1):
                entrada = ctk.CTkEntry(self.tabla, width=78, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
                entrada.insert(0, "0")
                entrada.grid(row=i + 1, column=j, padx=5, pady=4)
                fila.append(entrada)
            self.entradas.append(fila)

    def leer(self):
        datos = [[convertir_numero(entrada.get()) for entrada in fila] for fila in self.entradas]
        return [fila[:-1] for fila in datos], [fila[-1] for fila in datos]

    def limpiar(self):
        for fila in self.entradas:
            for entrada in fila:
                entrada.delete(0, "end")
                entrada.insert(0, "0")


class PanelProcedimiento(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.contenido = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.contenido.pack(fill="both", expand=True)
        self.placeholder()

    def limpiar(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    def placeholder(self):
        self.limpiar()
        ctk.CTkLabel(self.contenido, text="El procedimiento aparecerá aquí.", font=FUENTE_NORMAL, text_color=PALETA["texto_3"]).pack(anchor="w", padx=14, pady=14)

    def mostrar(self, pasos):
        self.limpiar()
        for indice, paso in enumerate(pasos):
            item = ctk.CTkFrame(self.contenido, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
            item.pack(fill="x", pady=(0, 12), padx=2)
            titulo = "Matriz aumentada inicial" if indice == 0 else f"Paso {indice}"
            ctk.CTkLabel(item, text=titulo, font=("Segoe UI", 12, "bold"), fg_color=PALETA["primario"], text_color="#04191A", corner_radius=6).pack(anchor="w", padx=14, pady=(10, 6))
            if indice:
                ctk.CTkLabel(item, text=f"Operación: {paso['operacion']}", font=FUENTE_NORMAL, text_color=PALETA["texto"]).pack(anchor="w", padx=14)
            ctk.CTkLabel(item, text=paso["explicacion"], font=FUENTE_PEQUENA, text_color=PALETA["texto_2"], wraplength=620, justify="left").pack(anchor="w", padx=14, pady=6)
            ctk.CTkLabel(item, text=matriz_a_texto(paso["matriz"]), font=FUENTE_MONO, text_color=PALETA["texto_2"], justify="left").pack(anchor="w", padx=14, pady=(0, 12))


class PanelResultado(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.contenido = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.contenido.pack(fill="both", expand=True)
        self.placeholder()

    def limpiar(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    def placeholder(self):
        self.limpiar()
        ctk.CTkLabel(self.contenido, text="El resultado aparecerá aquí.", font=FUENTE_NORMAL, text_color=PALETA["texto_3"]).pack(anchor="w", padx=14, pady=14)

    def mostrar(self, resultado):
        self.limpiar()
        clasificacion = resultado["clasificacion"]
        color = PALETA["error"] if "inconsistente" in clasificacion.lower() else PALETA["advertencia"] if "indeterminado" in clasificacion.lower() else PALETA["exito"]
        ctk.CTkLabel(self.contenido, text=clasificacion, font=("Segoe UI", 17, "bold"), text_color=color).pack(anchor="w", padx=14, pady=(14, 4))
        ctk.CTkLabel(self.contenido, text=resultado["descripcion"], font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", padx=14, pady=(0, 12))
        if resultado.get("solucion") is not None:
            valores = ", ".join(f"x{i + 1} = {formatear_numero(valor)}" for i, valor in enumerate(resultado["solucion"]))
            ctk.CTkLabel(self.contenido, text=valores, font=FUENTE_MONO, text_color=PALETA["primario"]).pack(anchor="w", padx=14, pady=4)
        elif resultado.get("expresiones") is not None:
            for indice, expresion in resultado["expresiones"].items():
                ctk.CTkLabel(self.contenido, text=f"x{indice + 1} = {expresion}", font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=14, pady=2)
        if resultado.get("verificacion"):
            correcta, detalles = resultado["verificacion"]
            texto = "Verificación correcta" if correcta else "La verificación falló"
            ctk.CTkLabel(self.contenido, text=texto, font=FUENTE_NORMAL, text_color=PALETA["exito"] if correcta else PALETA["error"]).pack(anchor="w", padx=14, pady=(12, 4))
            for detalle in detalles:
                ctk.CTkLabel(self.contenido, text=f"Ecuación {detalle.indice}: {detalle.suma_obtenida} = {detalle.esperado}", font=FUENTE_PEQUENA, text_color=PALETA["texto_2"]).pack(anchor="w", padx=24, pady=1)
