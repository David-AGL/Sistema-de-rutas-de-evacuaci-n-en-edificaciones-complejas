"""
application/emergency_mode.py

Caso de uso: aplicar bloqueos aleatorios al estado de evacuación
para simular una situación de emergencia real (incendio, escombros, humo).

Niveles de intensidad:
  - leve     → 1 nodo y 1 conexión bloqueados
  - moderada → 2 nodos y 2 conexiones bloqueados
  - critica  → 3 nodos y 4 conexiones bloqueados
"""

import random
from domain.graph import Graph
from domain.evacuation_state import EvacuationState


INTENSIDADES: dict[str, dict[str, int]] = {
    "leve":     {"nodos": 1, "aristas": 1},
    "moderada": {"nodos": 2, "aristas": 2},
    "critica":  {"nodos": 3, "aristas": 4},
}


def apply_emergency_blockages(
    graph: Graph,
    state: EvacuationState,
    intensidad: str = "moderada",
) -> dict[str, list]:
    """
    Aplica bloqueos aleatorios sobre el estado de evacuación según la intensidad.

    Restricciones:
      - Nunca bloquea nodos de tipo 'exit'.
      - Nunca bloquea una arista que conecte directamente a una salida
        (para garantizar que siempre exista al menos un camino posible).

    Args:
        graph:      El grafo del edificio cargado.
        state:      El estado de evacuación sobre el que se aplican los bloqueos.
        intensidad: 'leve', 'moderada' o 'critica'.

    Returns:
        Diccionario con las listas de nodos y aristas efectivamente bloqueados.

    Raises:
        ValueError: Si la intensidad no es válida.
    """
    if intensidad not in INTENSIDADES:
        raise ValueError(
            f"Intensidad inválida: '{intensidad}'. "
            f"Opciones: {', '.join(INTENSIDADES.keys())}"
        )

    config = INTENSIDADES[intensidad]

    # ── Nodos bloqueables: todos excepto salidas ──────────────────────
    nodos_bloqueables = [
        nid for nid, node in graph.nodes.items()
        if not node.is_exit()
    ]

    # ── Aristas bloqueables: no conectadas directamente a una salida ──
    # Usamos un set de pares ordenados para evitar duplicados
    aristas_vistas: set[tuple[str, str]] = set()
    aristas_bloqueables: list[tuple[str, str]] = []

    for nid, edges in graph.adjacency.items():
        for edge in edges:
            from_id, to_id = edge.from_id, edge.to_id
            par = (min(from_id, to_id), max(from_id, to_id))
            if par in aristas_vistas:
                continue
            aristas_vistas.add(par)
            # No bloquear si alguno de los extremos es salida
            if graph.get_node(from_id).is_exit() or graph.get_node(to_id).is_exit():
                continue
            aristas_bloqueables.append((from_id, to_id))

    # ── Aplicar bloqueos (sin exceder lo disponible) ──────────────────
    n_nodos   = min(config["nodos"],   len(nodos_bloqueables))
    n_aristas = min(config["aristas"], len(aristas_bloqueables))

    nodos_bloqueados   = random.sample(nodos_bloqueables,   n_nodos)
    aristas_bloqueadas = random.sample(aristas_bloqueables, n_aristas)

    for nid in nodos_bloqueados:
        state.block_node(nid)

    for (from_id, to_id) in aristas_bloqueadas:
        state.block_edge(from_id, to_id)

    return {
        "nodos":   nodos_bloqueados,
        "aristas": aristas_bloqueadas,
    }
