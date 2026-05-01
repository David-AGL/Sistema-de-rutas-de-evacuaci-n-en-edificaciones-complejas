"""
application/recommend_route.py

Responsabilidad: elegir la mejor ruta de evacuación entre varias opciones,
según un criterio definido.

Por qué existe este archivo y no está dentro de find_routes.py:
  find_routes.py  → ENCUENTRA rutas (exploración del grafo)
  recommend_route → EVALÚA y ELIGE entre ellas (toma de decisión)
  Son dos responsabilidades distintas.

Criterios disponibles:
  "costo"  → menor suma de pesos de aristas (tiempo/distancia real) [DEFAULT]
  "pasos"  → menor cantidad de nodos en la ruta (menos giros/puertas)
  "mixto"  → pondera ambos: 70% costo + 30% pasos normalizados
"""

from application.find_routes import Route


# ------------------------------------------------------------------ #
# Criterios de evaluación                                             #
# ------------------------------------------------------------------ #

def _score_costo(route: Route, max_cost: int, max_steps: int) -> float:
    """Criterio 1: menor costo acumulado (pesos de aristas)."""
    return float(route.cost)


def _score_pasos(route: Route, max_cost: int, max_steps: int) -> float:
    """Criterio 2: menor número de nodos recorridos."""
    return float(len(route.path))


def _score_mixto(route: Route, max_cost: int, max_steps: int) -> float:
    """
    Criterio 3: pondera costo y pasos normalizados.
    Normalizar permite comparar magnitudes distintas en la misma escala [0, 1].
      - costo normalizado = costo / max_costo_del_grupo
      - pasos normalizados = pasos / max_pasos_del_grupo
    Peso: 70% costo + 30% pasos.
    """
    costo_norm = route.cost / max_cost if max_cost > 0 else 0.0
    pasos_norm = len(route.path) / max_steps if max_steps > 0 else 0.0
    return 0.70 * costo_norm + 0.30 * pasos_norm


# Tabla de criterios disponibles
_CRITERIOS = {
    "costo": _score_costo,
    "pasos": _score_pasos,
    "mixto": _score_mixto,
}

CRITERIOS_VALIDOS = list(_CRITERIOS.keys())


# ------------------------------------------------------------------ #
# Función principal                                                   #
# ------------------------------------------------------------------ #

def recommend_route(routes: list[Route], criterio: str = "costo") -> Route | None:
    """
    Elige la mejor ruta de evacuación según el criterio indicado.

    Args:
        routes:   Lista de rutas obtenidas por FindRoutes.
        criterio: "costo" (default) | "pasos" | "mixto"

    Returns:
        La mejor Route según el criterio, o None si la lista está vacía.

    Raises:
        ValueError: Si el criterio no es válido.

    Ejemplos:
        recommend_route(routes)              → mejor por costo
        recommend_route(routes, "pasos")     → menos nodos
        recommend_route(routes, "mixto")     → balance costo + pasos
    """
    if not routes:
        return None

    if criterio not in _CRITERIOS:
        raise ValueError(
            f"Criterio '{criterio}' no válido. Usa: {CRITERIOS_VALIDOS}"
        )

    # Calcular los máximos del grupo (para normalización en criterio mixto)
    max_cost  = max(r.cost        for r in routes)
    max_steps = max(len(r.path)   for r in routes)

    score_fn = _CRITERIOS[criterio]

    # min() con la función de puntaje → menor puntaje = mejor ruta
    best = min(routes, key=lambda r: score_fn(r, max_cost, max_steps))

    return best


# ------------------------------------------------------------------ #
# Comparación entre criterios (útil para mostrar en CLI)             #
# ------------------------------------------------------------------ #

def comparar_criterios(routes: list[Route]) -> dict[str, Route]:
    """
    Retorna la mejor ruta según cada criterio disponible.
    Útil para mostrar al usuario qué elegiría cada estrategia.

    Returns:
        { "costo": Route, "pasos": Route, "mixto": Route }
    """
    if not routes:
        return {}

    return {
        criterio: recommend_route(routes, criterio)
        for criterio in CRITERIOS_VALIDOS
    }