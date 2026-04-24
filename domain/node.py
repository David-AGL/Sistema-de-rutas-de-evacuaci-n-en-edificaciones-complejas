"""
domain/node.py

Representa un nodo del grafo, que puede ser una habitación,
pasillo, escalera o salida dentro del edificio.
"""


class Node:
    """
    Un nodo es cualquier punto físico del edificio:
    habitación, pasillo, escalera o salida.
    """

    # Tipos válidos de nodo
    TYPES = {"room", "hallway", "staircase", "exit"}

    def __init__(self, node_id: str, label: str, node_type: str, level: int):
        """
        Args:
            node_id:   Identificador único del nodo. Ej: "A101", "P1N", "S1"
            label:     Nombre descriptivo.    Ej: "Aula 101", "Salida Principal"
            node_type: Categoría del nodo.    Ej: "room", "hallway", "exit"
            level:     Piso del edificio.     Ej: 1, 2
        """
        if node_type not in self.TYPES:
            raise ValueError(f"Tipo de nodo inválido: '{node_type}'. Usa: {self.TYPES}")

        self.id = node_id
        self.label = label
        self.type = node_type
        self.level = level

    def is_exit(self) -> bool:
        """Retorna True si este nodo es una salida del edificio."""
        return self.type == "exit"

    def __repr__(self) -> str:
        return f"Node({self.id!r}, '{self.label}', tipo={self.type}, piso={self.level})"