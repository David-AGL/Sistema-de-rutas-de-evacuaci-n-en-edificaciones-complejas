"""
application/block_path.py

Responsabilidad: encapsular las acciones de bloqueo y desbloqueo.

Por qué existe este archivo:
  El CLI no debería llamar directamente a state.block_node().
  Este módulo es la capa de aplicación que valida primero
  que el nodo/arista existe en el grafo antes de bloquearlo.
"""

from domain.graph import Graph
from domain.evacuation_state import EvacuationState


def block_node(graph: Graph, state: EvacuationState, node_id: str):
    """
    Bloquea un nodo si existe en el grafo.

    Raises:
        KeyError: Si node_id no existe en el grafo.
        ValueError: Si se intenta bloquear una salida
                    (bloquear la meta no tiene sentido).
    """
    node = graph.get_node(node_id)   # lanza KeyError si no existe

    if node.is_exit():
        raise ValueError(
            f"No se puede bloquear '{node_id}': es una salida de emergencia."
        )

    state.block_node(node_id)


def unblock_node(graph: Graph, state: EvacuationState, node_id: str):
    """Desbloquea un nodo si existe en el grafo."""
    graph.get_node(node_id)   # valida existencia
    state.unblock_node(node_id)


def block_edge(graph: Graph, state: EvacuationState, from_id: str, to_id: str):
    """
    Bloquea una arista si ambos nodos existen en el grafo.

    Raises:
        KeyError:  Si alguno de los nodos no existe.
        ValueError: Si no hay arista entre esos nodos.
    """
    graph.get_node(from_id)
    graph.get_node(to_id)

    # Verificar que la arista exista
    existe = any(e.to_id == to_id for e in graph.adjacency.get(from_id, []))
    if not existe:
        raise ValueError(f"No existe conexión entre '{from_id}' y '{to_id}'.")

    state.block_edge(from_id, to_id)


def unblock_edge(graph: Graph, state: EvacuationState, from_id: str, to_id: str):
    """Desbloquea una arista entre dos nodos."""
    graph.get_node(from_id)
    graph.get_node(to_id)
    state.unblock_edge(from_id, to_id)