"""
app.py

Orquestador principal del sistema de evacuación.

Responsabilidades:
  1. Escanear el directorio data/ y listar los edificios disponibles.
  2. Presentar un menú de selección de edificio.
  3. Permitir elegir entre modo normal y modo emergencia.
  4. En modo emergencia, aplicar bloqueos aleatorios según la intensidad elegida.
  5. Lanzar la interfaz CLI con el grafo y estado configurados.
  6. Al terminar, ofrecer volver al menú de edificios.

Lo que NO hace:
  - No tiene lógica de rutas ni de bloqueos manuales (eso es del CLI).
  - No modifica el grafo directamente.
"""

import json
from pathlib import Path

from infrastructure.persistence.building_loader import BuildingLoader
from domain.evacuation_state import EvacuationState
from interface.cli import run_cli
from application.emergency_mode import apply_emergency_blockages, INTENSIDADES


# ------------------------------------------------------------------ #
# Sección: descubrimiento de edificios                                #
# ------------------------------------------------------------------ #

def _listar_edificios(data_dir: str = "data") -> list[dict]:
    """
    Escanea el directorio data/ y devuelve la lista de edificios disponibles.

    Cada elemento es un dict con:
        path  : Path al archivo JSON
        name  : nombre del edificio leído desde el JSON
    """
    edificios = []
    for path in sorted(Path(data_dir).glob("*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("building", {}).get("name", path.stem)
        except Exception:
            name = path.stem
        edificios.append({"path": path, "name": name})
    return edificios


# ------------------------------------------------------------------ #
# Sección: menús de selección                                         #
# ------------------------------------------------------------------ #

def _menu_edificio(edificios: list[dict]) -> dict | None:
    """Muestra el menú de selección de edificio y retorna el elegido."""
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║       SISTEMA DE RUTAS DE EVACUACIÓN                ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    print("  Edificios disponibles:")
    for i, edificio in enumerate(edificios, 1):
        print(f"    [{i}] {edificio['name']}")
    print("    [0] Salir")
    print()

    while True:
        try:
            opcion = input("  Seleccione un edificio: ").strip()
        except KeyboardInterrupt:
            print()
            return None

        if opcion == "0":
            return None
        try:
            idx = int(opcion) - 1
            if 0 <= idx < len(edificios):
                return edificios[idx]
            print(f"  ✘ Ingresa un número entre 1 y {len(edificios)}.")
        except ValueError:
            print("  ✘ Opción inválida.")


def _menu_modo() -> str | None:
    """Permite elegir entre modo normal y modo emergencia."""
    print()
    print("  ══════════════════════════════════════════════════")
    print("  Modo de simulación:")
    print("    [1] Normal      — sin bloqueos iniciales")
    print("    [2] Emergencia  — bloqueos aleatorios al iniciar")
    print("    [0] Volver al menú de edificios")
    print("  ══════════════════════════════════════════════════")
    print()

    while True:
        try:
            opcion = input("  Seleccione modo: ").strip()
        except KeyboardInterrupt:
            print()
            return None

        if opcion == "0":
            return None
        if opcion == "1":
            return "normal"
        if opcion == "2":
            return "emergencia"
        print("  ✘ Opción inválida.")


def _menu_intensidad() -> str | None:
    """Permite elegir la intensidad del modo emergencia."""
    print()
    print("  Intensidad de la emergencia:")
    for nombre, config in INTENSIDADES.items():
        print(
            f"    - {nombre:<10} → "
            f"{config['nodos']} nodo(s) y "
            f"{config['aristas']} conexión(es) bloqueadas aleatoriamente"
        )
    print()

    while True:
        try:
            entrada = input("  Intensidad (Enter = 'moderada'): ").strip().lower()
        except KeyboardInterrupt:
            print()
            return None

        intensidad = entrada or "moderada"
        if intensidad in INTENSIDADES:
            return intensidad
        print(f"  ✘ Opciones válidas: {', '.join(INTENSIDADES.keys())}")


# ------------------------------------------------------------------ #
# Sección: arranque principal                                         #
# ------------------------------------------------------------------ #

def main():
    edificios = _listar_edificios("data")

    if not edificios:
        print("  ✘ No se encontraron edificios en el directorio 'data/'.")
        return

    while True:
        # ── 1. Selección de edificio ──────────────────────────────────
        edificio = _menu_edificio(edificios)
        if edificio is None:
            print("\n  Hasta luego.\n")
            break

        # ── 2. Cargar edificio ────────────────────────────────────────
        try:
            loader = BuildingLoader(str(edificio["path"]))
            graph  = loader.load()
        except (FileNotFoundError, KeyError, ValueError) as e:
            print(f"\n  ✘ Error al cargar el edificio: {e}\n")
            continue

        state = EvacuationState()

        # ── 3. Selección de modo ──────────────────────────────────────
        modo = _menu_modo()
        if modo is None:
            continue  # volver al menú de edificios

        # ── 4. Modo emergencia: aplicar bloqueos aleatorios ───────────
        if modo == "emergencia":
            intensidad = _menu_intensidad()
            if intensidad is None:
                continue  # volver al menú de edificios

            bloqueados = apply_emergency_blockages(graph, state, intensidad)

            print()
            print(f"  🚨 MODO EMERGENCIA ({intensidad.upper()}) ACTIVADO")

            if bloqueados["nodos"]:
                labels = [graph.get_node(nid).label for nid in bloqueados["nodos"]]
                print(f"  Nodos bloqueados   : {', '.join(labels)}")
            if bloqueados["aristas"]:
                labels = [
                    f"{graph.get_node(f).label} ↔ {graph.get_node(t).label}"
                    for (f, t) in bloqueados["aristas"]
                ]
                print(f"  Conexiones bloqueadas: {', '.join(labels)}")
            print()

        # ── 5. Lanzar la interfaz CLI ─────────────────────────────────
        run_cli(graph, state)

        # ── 6. Al terminar, ofrecer volver al menú de edificios ───────
        print()
        try:
            respuesta = input(
                "  ¿Volver al menú de edificios? (Enter = sí / n = salir): "
            ).strip().lower()
        except KeyboardInterrupt:
            respuesta = "n"

        if respuesta == "n":
            print("\n  Hasta luego.\n")
            break


if __name__ == "__main__":
    main()
