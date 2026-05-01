"""
application/find_routes.py

Responsabilidad: encontrar todas las rutas posibles desde un nodo
de inicio hacia cualquier salida del edificio, usando DFS con backtracking.

Reglas del algoritmo:
  - Nunca visita el mismo nodo dos veces en una misma ruta (evita ciclos).
  - Solo atraviesa aristas que no estén bloqueadas en el grafo ni en el estado.
  - Ignora nodos y aristas marcados como bloqueados en EvacuationState.
  - Se detiene cuando alcanza un nodo de tipo 'exit'.
  - Retorna TODAS las rutas válidas encontradas, ordenadas de menor a mayor costo.
"""

from domain.graph import Graph
from domain.node import Node
from domain.evacuation_state import EvacuationState


# ──────────────────────────────────────────────
# Estructura de resultado
# ──────────────────────────────────────────────

class Route:
    """
    Representa una ruta de evacuación completa.

    Atributos:
        path  : lista de IDs de nodos en orden de recorrido.
                Ej: ["A201", "P2N", "E1_2", "E1", "P1N", "S1"]
        cost  : suma de los pesos de todas las aristas recorridas.
        exits : ID del nodo de salida al final de la ruta.
    """

    def __init__(self, path: list[str], cost: int):
        self.path = path
        self.cost = cost
        self.exit_id = path[-1]   # el último nodo siempre es la salida

    def __repr__(self) -> str:
        ruta = " → ".join(self.path)
        return f"Route(costo={self.cost}, pasos={len(self.path)-1}: {ruta})"


# ──────────────────────────────────────────────
# Caso de uso principal
# ──────────────────────────────────────────────

class FindRoutes:
    """
    Caso de uso: encontrar todas las rutas de evacuación desde un nodo.

    Uso sin bloqueos:
        finder = FindRoutes(graph)
        routes = finder.find_all("A201")

    Uso con bloqueos dinámicos:
        finder = FindRoutes(graph, state)
        routes = finder.find_all("A201")
    """

    def __init__(self, graph: Graph, state: EvacuationState | None = None):
        self.graph = graph
        # Si no se pasa estado, se usa uno vacío (sin bloqueos)
        self.state = state if state is not None else EvacuationState()

    # ------------------------------------------------------------------ #
    # API pública                                                          #
    # ------------------------------------------------------------------ #

    def find_all(self, start_id: str) -> list[Route]:
        """
        Encuentra TODAS las rutas desde start_id hasta cualquier salida,
        respetando los bloqueos activos en EvacuationState.

        Args:
            start_id: ID del nodo desde donde empieza la evacuación.

        Returns:
            Lista de Route ordenada de menor a mayor costo.
            Lista vacía si no hay rutas o el nodo inicial está bloqueado.

        Raises:
            KeyError: Si start_id no existe en el grafo.
        """
        # Validar que el nodo de inicio exista
        self.graph.get_node(start_id)

        # Si el nodo inicial está bloqueado, no hay ninguna ruta posible
        if self.state.is_node_blocked(start_id):
            return []

        # Si el punto de inicio ya es una salida, retornar ruta trivial
        if self.graph.get_node(start_id).is_exit():
            return [Route(path=[start_id], cost=0)]

        results: list[Route] = []

        # Iniciar DFS con estado de bloqueos
        self._dfs(
            current_id=start_id,
            visited={start_id},
            path=[start_id],
            accumulated_cost=0,
            results=results
        )

        # Ordenar rutas de menor a mayor costo (la mejor primero)
        results.sort(key=lambda r: r.cost)

        return results

    def best_route(self, start_id: str) -> Route | None:
        """
        Retorna únicamente la ruta de menor costo desde start_id.

        Returns:
            La mejor Route, o None si no existe ninguna ruta.
        """
        routes = self.find_all(start_id)
        return routes[0] if routes else None

    # ------------------------------------------------------------------ #
    # DFS con backtracking (núcleo del algoritmo)                         #
    # ------------------------------------------------------------------ #

    def _dfs(
        self,
        current_id: str,
        visited: set[str],
        path: list[str],
        accumulated_cost: int,
        results: list[Route]
    ):
        """
        Explora recursivamente el grafo desde current_id.

        Parámetros:
            current_id       : nodo que estamos explorando ahora.
            visited          : nodos ya usados en esta ruta (evita ciclos).
            path             : ruta construida hasta este momento.
            accumulated_cost : suma de pesos recorridos hasta aquí.
            results          : lista compartida donde se guardan las rutas completas.

        Lógica central:
            1. Si el nodo actual es una salida → guardar ruta y retornar.
            2. Para cada vecino disponible (no bloqueado, no visitado):
                 a. Verificar que ni el nodo ni la arista estén bloqueados en state.
                 b. Agregar al path y a visitados.   ← avanzar
                 c. Llamar _dfs recursivamente.
                 d. Quitar del path y de visitados.  ← BACKTRACK
        """

        current_node = self.graph.get_node(current_id)

        # ── Caso base: llegamos a una salida ─────────────────────────────
        if current_node.is_exit():
            results.append(Route(path=list(path), cost=accumulated_cost))
            return

        # ── Paso recursivo: explorar vecinos ─────────────────────────────
        for edge in self.graph.get_neighbors(current_id):

            neighbor_id = edge.to_id

            # 1. Saltar nodos ya visitados en esta ruta → evita ciclos
            if neighbor_id in visited:
                continue

            # 2. Saltar nodos bloqueados por el estado de evacuación
            if self.state.is_node_blocked(neighbor_id):
                continue

            # 3. Saltar aristas bloqueadas por el estado de evacuación
            if self.state.is_edge_blocked(current_id, neighbor_id):
                continue

            # ── Avanzar ──────────────────────────────────────────────────
            visited.add(neighbor_id)
            path.append(neighbor_id)

            self._dfs(
                current_id=neighbor_id,
                visited=visited,
                path=path,
                accumulated_cost=accumulated_cost + edge.weight,
                results=results
            )

            # ── Backtrack: deshacer el paso para explorar otra rama ───────
            path.pop()
            visited.remove(neighbor_id)