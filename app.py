"""
app.py

Orquestador principal del sistema de evacuación.

Responsabilidad:
  1. Cargar el grafo desde el JSON
  2. Lanzar la interfaz CLI
"""

from infrastructure.persistence.building_loader import BuildingLoader
from interface.cli import run_cli


def main():
    # 1. Cargar el grafo desde el archivo JSON
    loader = BuildingLoader("data/building.json")
    graph  = loader.load()

    # 2. Pasar el grafo a la interfaz CLI
    run_cli(graph)


if __name__ == "__main__":
    main()