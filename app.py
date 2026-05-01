"""
app.py

Orquestador principal del sistema de evacuación.

Responsabilidad:
  1. Cargar el grafo desde el JSON
  2. Crear el estado inicial de evacuación (sin bloqueos)
  3. Lanzar la interfaz CLI

Lo que NO hace:
  - No tiene lógica de rutas
  - No tiene lógica de impresión
  - No tiene lógica de negocio
"""

from infrastructure.persistence.building_loader import BuildingLoader
from domain.evacuation_state import EvacuationState
from interface.cli import run_cli


def main():
    # 1. Cargar el grafo desde el archivo JSON
    loader = BuildingLoader("data/building.json")
    graph  = loader.load()

    # 2. Crear el estado de evacuación (empieza sin bloqueos)
    state = EvacuationState()

    # 3. Pasar grafo y estado a la interfaz CLI
    run_cli(graph, state)


if __name__ == "__main__":
    main()