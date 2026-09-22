import customtkinter as ctk
from interfaz.estilos import PALETA, FUENTE_NORMAL, FUENTE_SECCION


class PaginaMetodoEliminacion(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=PALETA["fondo"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Método de Eliminación de Gauss-Jordan", font=("Segoe UI", 26, "bold"), text_color=PALETA["texto"]).grid(row=0, column=0, sticky="w", padx=28, pady=(24, 12))
        cuerpo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        pasos = [
            ("1. Matriz aumentada [A | b]", "Se colocan juntos los coeficientes y los términos independientes."),
            ("2. Buscar el pivote", "Se busca un valor no nulo y se intercambian filas si es necesario."),
            ("3. Normalizar el pivote", "Se multiplica la fila para convertir el pivote en 1."),
            ("4. Eliminar la columna", "Se hacen cero los valores restantes de la columna pivote."),
            ("5. Repetir", "El proceso continúa hasta obtener la forma escalonada reducida."),
            ("6. Clasificar", "Se determina si el sistema tiene solución única, infinitas soluciones o ninguna."),
        ]
        for titulo, texto in pasos:
            tarjeta = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
            tarjeta.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(tarjeta, text=titulo, font=FUENTE_SECCION, text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 4))
            ctk.CTkLabel(tarjeta, text=texto, font=FUENTE_NORMAL, text_color=PALETA["texto_2"], wraplength=780, justify="left").pack(anchor="w", padx=16, pady=(0, 12))
