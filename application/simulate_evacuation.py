"""
application/simulate_evacuation.py

Simula la evacuación simultánea de múltiples personas desde diferentes ubicaciones.
- Asigna a cada persona una ruta usando FindRoutes + recommend_route
- Simula el movimiento paso a paso (un paso = un tramo de arista recorrido)
- Registra la ocupación de nodos y aristas en cada paso
- Detecta congestiones (dos o más personas en el mismo nodo al mismo tiempo)
"""

from dataclasses import dataclass, field
from application.find_routes import FindRoutes, Route
from application.recommend_route import recommend_route
from domain.graph import Graph
from domain.evacuation_state import EvacuationState


@dataclass
class Person:
    """Representa a una persona que será evacuada."""
    id: str
    name: str
    start_id: str
    route: Route | None = None
    evacuated: bool = False
    evacuation_time: int | None = None


@dataclass
class SimulationStep:
    """Instantánea de posiciones y eventos en un único paso de tiempo."""
    step: int
    positions: dict[str, str]        # person_id -> node_id actual
    congested_nodes: list[str]       # IDs de nodos con 2+ personas simultáneas
    newly_evacuated: list[str]       # IDs de personas que evacuaron en este paso


@dataclass
class SimulationResult:
    """Resultados completos de una simulación de evacuación multi-persona."""
    personas: list[Person]
    steps: list[SimulationStep]
    node_traffic: dict[str, int]                        # node_id -> total de pases
    edge_traffic: dict[tuple[str, str], int]            # (from, to) -> total de pases
    congestion_nodes: list[tuple[str, int]]             # (node_id, pico) ordenado desc
    congestion_edges: list[tuple[tuple[str, str], int]] # ((from, to), count) ord. desc
    total_steps: int
    unresolved: list[str]                               # IDs de personas sin ruta


class SimulateEvacuation:
    """
    Simula la evacuación de múltiples personas de manera simultánea.

    Uso:
        sim = SimulateEvacuation(graph, state)
        sim.add_person("P1", "María", "A201")
        sim.add_person("P2", "Juan", "A101")
        result = sim.run()
    """

    def __init__(self, graph: Graph, state: EvacuationState):
        self.graph = graph
        self.state = state
        self.personas: list[Person] = []

    def add_person(self, person_id: str, name: str, start_id: str) -> None:
        """Registra una persona para incluir en la simulación."""
        self.personas.append(Person(id=person_id, name=name, start_id=start_id))

    def clear(self) -> None:
        """Elimina todas las personas registradas (permite reutilizar la instancia)."""
        self.personas.clear()

    def run(self, criterio: str = "costo") -> SimulationResult:
        """
        Ejecuta la simulación completa.

        Cada paso representa un movimiento: la persona avanza un nodo a lo largo
        de su ruta asignada. Todos los participantes se mueven simultáneamente.

        Args:
            criterio: Criterio de selección de ruta — 'costo', 'pasos' o 'mixto'.

        Returns:
            SimulationResult con snapshots por paso, tráfico y datos de congestión.
        """
        if not self.personas:
            return SimulationResult(
                personas=[], steps=[], node_traffic={}, edge_traffic={},
                congestion_nodes=[], congestion_edges=[], total_steps=0, unresolved=[]
            )

        # ── 1. Asignar rutas ──────────────────────────────────────────────
        finder = FindRoutes(self.graph, self.state)
        unresolved: list[str] = []

        for persona in self.personas:
            routes = finder.find_all(persona.start_id)
            if routes:
                try:
                    persona.route = recommend_route(routes, criterio)
                except ValueError:
                    persona.route = routes[0]
            else:
                unresolved.append(persona.id)

        active = [p for p in self.personas if p.route is not None]

        if not active:
            return SimulationResult(
                personas=self.personas, steps=[], node_traffic={}, edge_traffic={},
                congestion_nodes=[], congestion_edges=[], total_steps=0,
                unresolved=unresolved
            )

        # ── 2. Simular paso a paso ────────────────────────────────────────
        node_traffic: dict[str, int] = {}
        edge_traffic: dict[tuple[str, str], int] = {}
        peak_node_occupancy: dict[str, int] = {}
        simulation_steps: list[SimulationStep] = []

        max_route_len = max(len(p.route.path) for p in active)

        for step in range(max_route_len):
            positions: dict[str, str] = {}
            node_occupancy: dict[str, list[str]] = {}  # node_id -> [person_ids]
            newly_evacuated: list[str] = []

            for persona in active:
                if persona.evacuated:
                    continue

                path = persona.route.path
                if step >= len(path):
                    continue

                node_id = path[step]
                positions[persona.id] = node_id
                node_occupancy.setdefault(node_id, []).append(persona.id)
                node_traffic[node_id] = node_traffic.get(node_id, 0) + 1

                # Registrar tráfico de arista (movimiento desde nodo anterior)
                if step > 0:
                    prev = path[step - 1]
                    key: tuple[str, str] = (prev, node_id)
                    edge_traffic[key] = edge_traffic.get(key, 0) + 1

                # Verificar si llegó a una salida
                if self.graph.get_node(node_id).is_exit():
                    persona.evacuated = True
                    persona.evacuation_time = step
                    newly_evacuated.append(persona.id)

            # Actualizar pico de ocupación
            for node_id, occupants in node_occupancy.items():
                count = len(occupants)
                if count > peak_node_occupancy.get(node_id, 0):
                    peak_node_occupancy[node_id] = count

            congested = [nid for nid, occ in node_occupancy.items() if len(occ) > 1]

            simulation_steps.append(SimulationStep(
                step=step,
                positions=dict(positions),
                congested_nodes=congested,
                newly_evacuated=newly_evacuated,
            ))

        # ── 3. Calcular resumen de congestiones ───────────────────────────
        congestion_nodes = sorted(
            [(nid, count) for nid, count in peak_node_occupancy.items() if count > 1],
            key=lambda x: -x[1]
        )
        congestion_edges = sorted(
            [(key, count) for key, count in edge_traffic.items() if count >= 2],
            key=lambda x: -x[1]
        )

        return SimulationResult(
            personas=self.personas,
            steps=simulation_steps,
            node_traffic=node_traffic,
            edge_traffic=edge_traffic,
            congestion_nodes=congestion_nodes,
            congestion_edges=congestion_edges,
            total_steps=max_route_len - 1,
            unresolved=unresolved,
        )
