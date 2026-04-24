"""
test_loader.py  (script temporal de prueba — ejecutar desde la raíz del proyecto)

Verifica que BuildingLoader lee el JSON y construye el grafo correctamente.
"""

import sys
sys.path.insert(0, ".")   # permite importar domain/ e infrastructure/ desde la raíz

from infrastructure.persistence.building_loader import BuildingLoader

print("=" * 50)
print("  Cargando edificio desde data/building.json")
print("=" * 50)

loader = BuildingLoader("data/building.json")
graph  = loader.load()

print()
print(graph.summary())

print()
print("── Salidas disponibles ──────────────────────")
for exit_node in graph.get_exits():
    print(f"  • {exit_node}")

print()
print("── Vecinos de A201 (Aula 201, piso 2) ──────")
for edge in graph.get_neighbors("A201"):
    print(f"  → {edge}")

print()
print("── Simulando bloqueo del pasillo norte P1N → S1 ──")
graph.block_edge("P1N", "S1")
vecinos = graph.get_neighbors("P1N")
print(f"  Vecinos de P1N tras bloqueo: {[e.to_id for e in vecinos]}")

print()
print("  ✔ Prueba completada con éxito.")