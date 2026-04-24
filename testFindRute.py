"""
test_find_routes.py  (ejecutar desde la raíz del proyecto)

Prueba el algoritmo de búsqueda de rutas en tres escenarios:
  1. Rutas normales desde el piso 2.
  2. Rutas con un bloqueo activo.
  3. Caso sin salida posible (todo bloqueado).
"""

import sys
sys.path.insert(0, ".")

from infrastructure.persistence.building_loader import BuildingLoader
from application.find_routes import FindRoutes


def separador(titulo: str):
    print()
    print("=" * 55)
    print(f"  {titulo}")
    print("=" * 55)


# ── Cargar edificio ───────────────────────────────────────────
separador("Cargando edificio")
loader = BuildingLoader("data/building.json")
graph  = loader.load()
finder = FindRoutes(graph)


# ── Escenario 1: todas las rutas desde Aula 201 ───────────────
separador("Escenario 1 — Rutas desde A201 (Aula 201, piso 2)")

rutas = finder.find_all("A201")

if rutas:
    print(f"  Se encontraron {len(rutas)} ruta(s):\n")
    for i, ruta in enumerate(rutas, 1):
        print(f"  [{i}] Costo: {ruta.cost:>3}  |  {' → '.join(ruta.path)}")
    print()
    mejor = rutas[0]
    print(f"  ★ Mejor ruta: {' → '.join(mejor.path)}  (costo {mejor.cost})")
else:
    print("  ✘ No se encontraron rutas.")


# ── Escenario 2: bloquear escalera principal ──────────────────
separador("Escenario 2 — Bloqueo en E1_2 → E1 (escalera principal)")

graph.block_edge("E1_2", "E1")
print("  Arista E1_2 ↔ E1 bloqueada.\n")

rutas_bloqueadas = finder.find_all("A201")

if rutas_bloqueadas:
    print(f"  Se encontraron {len(rutas_bloqueadas)} ruta(s):\n")
    for i, ruta in enumerate(rutas_bloqueadas, 1):
        print(f"  [{i}] Costo: {ruta.cost:>3}  |  {' → '.join(ruta.path)}")
    mejor = rutas_bloqueadas[0]
    print(f"\n  ★ Mejor ruta alternativa: {' → '.join(mejor.path)}  (costo {mejor.cost})")
else:
    print("  ✘ No se encontraron rutas con ese bloqueo.")


# ── Escenario 3: bloquear también la escalera de emergencia ───
separador("Escenario 3 — Bloqueo total de escaleras desde piso 2")

graph.block_edge("E2_2", "E2")
print("  Arista E2_2 ↔ E2 también bloqueada.\n")

rutas_sin_salida = finder.find_all("A201")

if rutas_sin_salida:
    print(f"  Se encontraron {len(rutas_sin_salida)} ruta(s).")
else:
    print("  ✘ No hay rutas disponibles. ¡El piso 2 está completamente aislado!")

print()
print("  ✔ Todas las pruebas completadas.")