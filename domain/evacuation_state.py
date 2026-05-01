"""
domain/evacuation_state.py

Responsabilidad: guardar el estado dinámico de la evacuación.
  - Qué nodos están bloqueados (fuego, derrumbe, humo, etc.)
  - Qué aristas están bloqueadas (puerta trabada, corredor inundado, etc.)

Por qué existe este archivo:
  El grafo (graph.py) modela la estructura FIJA del edificio.
  Este estado modela lo que cambia DURANTE la emergencia.
  Así el grafo nunca se modifica: podemos resetear el estado
  sin tener que recargar el JSON.
"""


class EvacuationState:
    """
    Estado mutable de la evacuación.
    Registra bloqueos de nodos y aristas de forma independiente al grafo.
    """

    def __init__(self):
        # Conjunto de IDs de nodos bloqueados
        self.blocked_nodes: set[str] = set()

        # Conjunto de tuplas (from_id, to_id) de aristas bloqueadas
        # Se guarda en ambas direcciones para facilitar la consulta
        self.blocked_edges: set[tuple[str, str]] = set()

    # ------------------------------------------------------------------ #
    # Bloqueo de nodos                                                     #
    # ------------------------------------------------------------------ #

    def block_node(self, node_id: str):
        """Bloquea un nodo: ninguna ruta podrá pasar por él."""
        self.blocked_nodes.add(node_id)

    def unblock_node(self, node_id: str):
        """Desbloquea un nodo previamente bloqueado."""
        self.blocked_nodes.discard(node_id)   # discard no lanza error si no existe

    def is_node_blocked(self, node_id: str) -> bool:
        """Retorna True si el nodo está bloqueado."""
        return node_id in self.blocked_nodes

    # ------------------------------------------------------------------ #
    # Bloqueo de aristas                                                   #
    # ------------------------------------------------------------------ #

    def block_edge(self, from_id: str, to_id: str):
        """Bloquea la conexión entre dos nodos en ambas direcciones."""
        self.blocked_edges.add((from_id, to_id))
        self.blocked_edges.add((to_id, from_id))

    def unblock_edge(self, from_id: str, to_id: str):
        """Desbloquea la conexión entre dos nodos."""
        self.blocked_edges.discard((from_id, to_id))
        self.blocked_edges.discard((to_id, from_id))

    def is_edge_blocked(self, from_id: str, to_id: str) -> bool:
        """Retorna True si la arista entre esos dos nodos está bloqueada."""
        return (from_id, to_id) in self.blocked_edges

    # ------------------------------------------------------------------ #
    # Utilidades                                                           #
    # ------------------------------------------------------------------ #

    def reset(self):
        """Limpia todos los bloqueos. Útil para iniciar una nueva simulación."""
        self.blocked_nodes.clear()
        self.blocked_edges.clear()

    def has_blocks(self) -> bool:
        """Retorna True si hay al menos un bloqueo activo."""
        return bool(self.blocked_nodes or self.blocked_edges)

    def summary(self) -> str:
        """Describe el estado actual de los bloqueos."""
        if not self.has_blocks():
            return "Sin bloqueos activos."
        lines = []
        if self.blocked_nodes:
            lines.append(f"  🚫 Nodos bloqueados : {', '.join(sorted(self.blocked_nodes))}")
        if self.blocked_edges:
            pares = [f"{a}↔{b}" for a, b in self.blocked_edges if a < b]
            lines.append(f"  🚧 Conexiones bloqueadas: {', '.join(sorted(pares))}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (f"EvacuationState("
                f"nodos_bloqueados={self.blocked_nodes}, "
                f"aristas_bloqueadas={self.blocked_edges})")