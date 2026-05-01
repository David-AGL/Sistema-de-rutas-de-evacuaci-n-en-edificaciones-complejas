"""
application/compare_routes.py

Responsabilidad: calcular métricas detalladas sobre cada ruta
y producir una comparación estructurada entre ellas.

Por qué existe este archivo y no está en find_routes.py o recommend_route.py:
  find_routes.py     → ENCUENTRA rutas (algoritmo DFS)
  recommend_route.py → ELIGE la mejor ruta (decisión)
  compare_routes.py  → DESCRIBE y CONTRASTA las rutas (análisis)

Las métricas que calcula este módulo NO estaban disponibles en Route,
porque Route solo guarda lo mínimo necesario para el algoritmo.
Las métricas son una capa de análisis encima de ese resultado.
"""

from dataclasses import dataclass
from application.find_routes import Route
from domain.graph import Graph


# ------------------------------------------------------------------ #
# Constantes de tipos de nodo                                        #
# ------------------------------------------------------------------ #
# Estos valores deben coincidir con los usados en domain/node.py
NODE_TYPE_STAIRCASE = "staircase"
NODE_TYPE_HALLWAY = "hallway"


# ------------------------------------------------------------------ #
# Estructura de métricas por ruta                                     #
# ------------------------------------------------------------------ #

@dataclass
class RouteMetrics:
    """
    Métricas derivadas de una ruta. Se calculan a partir de Route + Graph.

    NOTA sobre Route:
        Route es importado desde application.find_routes.
        Estructura esperada: Route(path: list[str], cost: int, exit_id: str)
        - path: lista de IDs de nodos (str) del inicio a salida
        - cost: suma de pesos de aristas recorridas
        - exit_id: ID del nodo de salida destino

    Atributos:
        rank         : posición en el ranking (1 = mejor por costo).
        route        : objeto Route original (contiene path, cost, exit_id).
        pasos        : cantidad de tramos recorridos (len(path) - 1).
        costo        : suma de pesos de aristas (del objeto route).
        n_escaleras  : cuántas escaleras hay en el recorrido.
        n_pasillos   : cuántos pasillos hay en el recorrido.
        salida_label : nombre legible de la salida destino.
        eficiencia   : costo / pasos → costo promedio por tramo.
                       Menor = tramos más cortos en promedio.
                       Si pasos == 0 (ruta trivial), se asigna 0.0.
        etiquetas    : lista de nombres legibles de cada nodo en el recorrido.
    """
    rank         : int
    route        : Route
    pasos        : int
    costo        : int
    n_escaleras  : int
    n_pasillos   : int
    salida_label : str
    eficiencia   : float
    etiquetas    : list[str]


# ------------------------------------------------------------------ #
# Función principal                                                   #
# ------------------------------------------------------------------ #

def compare_routes(routes: list[Route], graph: Graph) -> list[RouteMetrics]:
    """
    Calcula métricas detalladas para cada ruta y las retorna ordenadas
    de menor a mayor costo (rank 1 = mejor).

    Args:
        routes : lista de Route obtenida de FindRoutes.find_all().
        graph  : grafo del edificio (para consultar tipo de cada nodo).

    Returns:
        Lista de RouteMetrics, una por ruta, ordenada por costo (ascendente).
        Lista vacía si routes está vacía.

    Raises:
        ValueError: Si alguna ruta tiene un path inválido (nodos no existen)
                   o si exit_id no existe en el grafo.

    Nota:
        Este módulo NO modifica el grafo ni las rutas, solo analiza.
        Si hay rutas problemáticas, lanza excepción (fail-fast).
    """
    if not routes:
        return []

    # Ordenar por costo para asignar ranks correctamente
    ordenadas = sorted(routes, key=lambda r: r.cost)

    metricas = []
    for rank, route in enumerate(ordenadas, start=1):
        metricas.append(_calcular_metricas(rank, route, graph))

    return metricas


def _calcular_metricas(rank: int, route: Route, graph: Graph) -> RouteMetrics:
    """
    Deriva todas las métricas de una Route usando el grafo.

    Validaciones:
    - Filtra nodos None (en caso de IDs inválidos).
    - Valida que exit_id exista en el grafo.
    - Maneja división por cero cuando pasos == 0 (rutas triviales).

    Raises:
        ValueError: Si exit_id no existe en el grafo o no tiene label.
    """
    # Obtener nodos válidos (filtra None si algún ID no existe)
    nodos = [graph.get_node(nid) for nid in route.path if graph.get_node(nid) is not None]

    # Si no hay nodos válidos, es una ruta problemática
    if not nodos:
        raise ValueError(f"Ruta con path {route.path} no tiene nodos válidos en el grafo")

    n_escaleras = sum(1 for n in nodos if n.type == NODE_TYPE_STAIRCASE)
    n_pasillos  = sum(1 for n in nodos if n.type == NODE_TYPE_HALLWAY)
    pasos       = len(route.path) - 1
    
    # División por cero: ocurre si pasos == 0 (ruta trivial: inicio == salida)
    eficiencia  = round(route.cost / pasos, 2) if pasos > 0 else 0.0
    
    etiquetas   = [n.label for n in nodos]
    
    # Validar que exit_id existe y tiene label
    exit_node = graph.get_node(route.exit_id)
    if exit_node is None:
        raise ValueError(f"exit_id {route.exit_id} no existe en el grafo")
    if not hasattr(exit_node, 'label') or exit_node.label is None:
        raise ValueError(f"exit_id {route.exit_id} no tiene label válido")
    
    salida = exit_node.label

    return RouteMetrics(
        rank         = rank,
        route        = route,
        pasos        = pasos,
        costo        = route.cost,
        n_escaleras  = n_escaleras,
        n_pasillos   = n_pasillos,
        salida_label = salida,
        eficiencia   = eficiencia,
        etiquetas    = etiquetas,
    )


# ------------------------------------------------------------------ #
# Vista tabular para CLI                                              #
# ------------------------------------------------------------------ #

def formato_tabla(metricas: list[RouteMetrics]) -> str:
    """
    Genera una tabla comparativa en texto plano lista para imprimir.

    Ejemplo de salida:
      #  Ruta                              Costo  Pasos  Escaleras  Efic.  Salida
      ─────────────────────────────────────────────────────────────────────────────
      1★ A201→P2N→E1_2→E1→P1N→S1              7      5          2   1.40  Salida Principal
      2  A201→P2N→P2S→E2_2→E2→P1S→S2          9      6          2   1.50  Salida Emergencia
    """
    if not metricas:
        return "  (sin rutas para comparar)"

    # Encabezado
    # Usar ancho amplio + ASCII evita corrimientos visuales en algunas terminales.
    col_ruta = 50
    lineas = [
        f"  {'#':<3} {'Ruta':<{col_ruta}} {'Costo':>5}  {'Pasos':>5}  "
        f"{'Escal.':>6}  {'Efic.':>5}  Salida",
        "  " + "-" * (col_ruta + 35),
    ]

    for m in metricas:
        path = m.route.path if isinstance(m.route.path, list) else []
        ruta_ids = " -> ".join(path)
        # Truncar si es muy largo para que quepa en la tabla
        if len(ruta_ids) > col_ruta:
            ruta_ids = ruta_ids[:col_ruta - 3] + "..."

        # Saneo defensivo para evitar huecos visuales si llega un tipo inesperado.
        costo = m.costo if isinstance(m.costo, int) else 0
        pasos = m.pasos if isinstance(m.pasos, int) else 0
        n_escaleras = m.n_escaleras if isinstance(m.n_escaleras, int) else 0
        eficiencia = m.eficiencia if isinstance(m.eficiencia, (int, float)) else 0.0

        marca = "★" if m.rank == 1 else " "
        lineas.append(
            f"  {m.rank}{marca} {ruta_ids.ljust(col_ruta)} {costo:>5}  {pasos:>5}  "
            f"{n_escaleras:>6}  {eficiencia:>5.2f}  {m.salida_label}"
        )

    return "\n".join(lineas)


def formato_detalle(m: RouteMetrics) -> str:
    """
    Genera el detalle completo de una ruta (usado al seleccionar una fila).
    """
    lineas = [
        f"  Ruta #{m.rank}{'  ★ MEJOR COSTO' if m.rank == 1 else ''}",
        f"  IDs      : {' → '.join(m.route.path)}",
        f"  Detalle  : {' → '.join(m.etiquetas)}",
        f"  Costo    : {m.costo}",
        f"  Pasos    : {m.pasos}",
        f"  Escaleras: {m.n_escaleras}",
        f"  Pasillos : {m.n_pasillos}",
        f"  Eficiencia (costo/paso): {m.eficiencia}",
        f"  Salida   : {m.salida_label}",
    ]
    return "\n".join(lineas)