"""Estructuras de datos que viajan entre la logica y la interfaz."""


class PasoEliminacion(dict):
    """Una operacion elemental, su explicacion y la matriz resultante."""

    def __init__(self, operacion, explicacion, matriz, tipo="operacion"):
        super().__init__(operacion=operacion, explicacion=explicacion, matriz=matriz, tipo=tipo)
        self.operacion = operacion
        self.explicacion = explicacion
        self.matriz = matriz
        self.tipo = tipo

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self["operacion"]
            if key == 1:
                return self["matriz"]
            if key == 2:
                return self["explicacion"]
            raise IndexError("Indice de paso fuera de rango (0-2)")
        return super().__getitem__(key)


class DetalleVerificacion(dict):
    """Resultado detallado de comprobar una ecuacion original."""

    def __init__(self, indice, ecuacion_original, sustitucion, simplificacion, suma_obtenida, esperado, coincide):
        super().__init__(indice=indice, ecuacion_original=ecuacion_original, sustitucion=sustitucion, simplificacion=simplificacion, suma_obtenida=suma_obtenida, esperado=esperado, coincide=coincide)
        self.indice = indice
        self.ecuacion_original = ecuacion_original
        self.sustitucion = sustitucion
        self.simplificacion = simplificacion
        self.suma_obtenida = suma_obtenida
        self.esperado = esperado
        self.coincide = coincide

    def __getitem__(self, key):
        if isinstance(key, int):
            return [self["suma_obtenida"], self["esperado"], self["coincide"]][key]
        return super().__getitem__(key)
