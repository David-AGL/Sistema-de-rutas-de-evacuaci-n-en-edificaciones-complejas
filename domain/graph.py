"""
domain/graph.py

Representa el grafo completo del edificio.
Gestiona nodos, aristas y consultas sobre la estructura.
"""

from domain.node import Node
from domain.edge import Edge


class Graph:
    """
    Grafo no dirigido que modela el edificio.
    Cada nodo es un espacio físico; cada arista, una conexión entre espacios.
    Las aristas son bidireccionales: si A conecta con B, también B conecta con A.
    """

    def __init__(self):
        self.nodes: dict[str, Node] = {}          # id → Node
        self.adjacency: dict[str, list[Edge]] = {}  # id → [Edge, ...]

    # ------------------------------------------------------------------ #
    # Construcción del grafo                                               #
    # ------------------------------------------------------------------ #

    def add_node(self, node: Node):
        """Agrega un nodo al grafo."""
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []

    def add_edge(self, edge: Edge):
        """
        Agrega una arista bidireccional al grafo.
        Se crean dos entradas: A→B y B→A.
        """
        # Dirección A → B
        self.adjacency[edge.from_id].append(edge)

        # Dirección B → A (arista inversa con los mismos atributos)
        reverse = Edge(
            from_id=edge.to_id,
            to_id=edge.from_id,
            weight=edge.weight,
            description=edge.description
        )
        # Sincronizar el estado de bloqueo: ambas apuntan al mismo objeto
        # para que al bloquear una, la inversa también quede bloqueada.
        # Lo resolvemos guardando referencia a la arista original.
        reverse._pair = edge      # referencia al par
        edge._pair = reverse

        self.adjacency[edge.to_id].append(reverse)

    # ------------------------------------------------------------------ #
    # Consultas                                                            #
    # ------------------------------------------------------------------ #

    def get_node(self, node_id: str) -> Node:
        """Retorna el nodo con ese ID. Lanza error si no existe."""
        if node_id not in self.nodes:
            raise KeyError(f"Nodo '{node_id}' no encontrado en el grafo.")
        return self.nodes[node_id]

    def get_neighbors(self, node_id: str) -> list[Edge]:
        """
        Retorna las aristas disponibles (no bloqueadas) desde un nodo.
        Solo incluye conexiones por las que se puede transitar.
        """
        return [
            edge for edge in self.adjacency.get(node_id, [])
            if edge.is_available()
        ]

    def get_exits(self) -> list[Node]:
        """Retorna todos los nodos de tipo 'exit' del edificio."""
        return [node for node in self.nodes.values() if node.is_exit()]

    def block_edge(self, from_id: str, to_id: str):
        """
        Bloquea la conexión entre dos nodos en ambas direcciones.
        Simula un obstáculo dinámico (fuego, derrumbe, etc.).
        """
        for edge in self.adjacency.get(from_id, []):
            if edge.to_id == to_id:
                edge.block()
                if hasattr(edge, "_pair"):
                    edge._pair.block()
                return
        raise ValueError(f"No existe arista entre '{from_id}' y '{to_id}'.")

    def unblock_edge(self, from_id: str, to_id: str):
        """Desbloquea la conexión entre dos nodos en ambas direcciones."""
        for edge in self.adjacency.get(from_id, []):
            if edge.to_id == to_id:
                edge.unblock()
                if hasattr(edge, "_pair"):
                    edge._pair.unblock()
                return
        raise ValueError(f"No existe arista entre '{from_id}' y '{to_id}'.")

    # ------------------------------------------------------------------ #
    # Representación                                                       #
    # ------------------------------------------------------------------ #

    def summary(self) -> str:
        """Muestra un resumen del grafo: nodos, aristas y salidas."""
        total_edges = sum(len(v) for v in self.adjacency.values()) // 2
        exits = [n.label for n in self.get_exits()]
        lines = [
            f"Edificio cargado:",
            f"  • Nodos    : {len(self.nodes)}",
            f"  • Aristas  : {total_edges}",
            f"  • Salidas  : {exits}",
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Graph(nodos={len(self.nodes)}, salidas={len(self.get_exits())})"