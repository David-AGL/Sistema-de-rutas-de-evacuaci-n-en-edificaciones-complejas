"""
domain/edge.py

Representa una arista (conexión) entre dos nodos del grafo.
Puede estar bloqueada dinámicamente (ej: fuego, derrumbe).
"""


class Edge:
    """
    Una arista conecta dos nodos del edificio.
    Tiene un peso (tiempo/costo de recorrerla) y puede bloquearse.
    """

    def __init__(self, from_id: str, to_id: str, weight: int = 1, description: str = ""):
        """
        Args:
            from_id:     ID del nodo de origen.
            to_id:       ID del nodo de destino.
            weight:      Costo de recorrer esta conexión (1 = fácil, 3 = lento).
            description: Descripción legible de la conexión.
        """
        if weight <= 0:
            raise ValueError(f"El peso debe ser mayor a 0. Recibido: {weight}")

        self.from_id = from_id
        self.to_id = to_id
        self.weight = weight
        self.description = description
        self.blocked = False  # Por defecto, la conexión está libre

    def block(self):
        """Bloquea esta conexión (ej: hay fuego o derrumbe en este tramo)."""
        self.blocked = True

    def unblock(self):
        """Desbloquea esta conexión (emergencia despejada)."""
        self.blocked = False

    def is_available(self) -> bool:
        """Retorna True si la conexión puede usarse (no está bloqueada)."""
        return not self.blocked

    def __repr__(self) -> str:
        estado = "BLOQUEADA" if self.blocked else "libre"
        return f"Edge({self.from_id!r} → {self.to_id!r}, peso={self.weight}, {estado})"