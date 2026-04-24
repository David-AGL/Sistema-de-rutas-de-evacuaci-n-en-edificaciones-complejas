"""
interface/cli.py

Responsabilidad: interactuar con el usuario por consola.
  - Pide la ubicación de inicio
  - Valida que el nodo exista
  - Llama al caso de uso FindRoutes
  - Muestra los resultados formateados
"""

from application.find_routes import FindRoutes
from domain.graph import Graph


def run_cli(graph: Graph):
    """
    Punto de entrada de la interfaz de línea de comandos.
    Recibe el grafo ya cargado y gestiona la sesión con el usuario.
    """
    _print_header(graph)

    while True:
        start = _pedir_ubicacion(graph)

        if start is None:
            break

        _buscar_y_mostrar(graph, start)

        if not _continuar():
            break

    print("\n  Cerrando sistema de evacuación. ¡Mantén la calma!\n")


# ------------------------------------------------------------------ #
# Funciones internas de apoyo                                         #
# ------------------------------------------------------------------ #

def _print_header(graph: Graph):
    """Muestra el encabezado del sistema al iniciar."""
    salidas = [n.label for n in graph.get_exits()]
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║       SISTEMA DE RUTAS DE EVACUACIÓN                ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"  Edificio cargado con {len(graph.nodes)} nodos.")
    print(f"  Salidas registradas: {', '.join(salidas)}")
    print()
    print("  Nodos disponibles:")
    _listar_nodos(graph)
    print()


def _listar_nodos(graph: Graph):
    """Imprime todos los nodos agrupados por piso."""
    por_piso: dict[int, list] = {}
    for node in graph.nodes.values():
        por_piso.setdefault(node.level, []).append(node)

    iconos = {"room": "🚪", "hallway": "🚶", "staircase": "🪜", "exit": "🚪✅"}

    for nivel in sorted(por_piso):
        print(f"  Piso {nivel}:")
        for node in por_piso[nivel]:
            icono = iconos.get(node.type, "•")
            print(f"    {icono}  [{node.id:<6}]  {node.label}")


def _pedir_ubicacion(graph: Graph) -> str | None:
    """
    Solicita al usuario un ID de nodo válido.
    Retorna el ID si es válido, o None si el usuario quiere salir.
    """
    while True:
        print()
        entrada = input("  Ingrese su ubicación actual (ID del nodo) o 'salir': ").strip()

        if entrada.lower() == "salir":
            return None

        if entrada in graph.nodes:
            nodo = graph.get_node(entrada)
            print(f"  ✔ Ubicación confirmada: {nodo.label} (Piso {nodo.level})")
            return entrada

        print(f"  ✘ '{entrada}' no existe en el edificio. Intente de nuevo.")


def _buscar_y_mostrar(graph: Graph, start_id: str):
    """Llama a FindRoutes y muestra los resultados al usuario."""
    finder = FindRoutes(graph)
    routes = finder.find_all(start_id)

    print()
    print("  ┌─────────────────────────────────────────────────┐")

    if not routes:
        print("  │  ✘ No hay rutas disponibles desde esta ubicación.")
        print("  │    Todas las salidas están bloqueadas.")
        print("  └─────────────────────────────────────────────────┘")
        return

    print(f"  │  Se encontraron {len(routes)} ruta(s) de evacuación:")
    print("  └─────────────────────────────────────────────────┘")
    print()

    for i, route in enumerate(routes, 1):
        # Enriquecer el path con etiquetas legibles
        etiquetas = [graph.get_node(nid).label for nid in route.path]
        ruta_str  = " → ".join(route.path)
        salida    = graph.get_node(route.exit_id).label

        prefijo = "  ★ " if i == 1 else f"  {i}.  "
        nota    = "  ← MEJOR RUTA" if i == 1 else ""

        print(f"{prefijo}[Costo: {route.cost:>3}]  {ruta_str}{nota}")
        print(f"       Descripción: {' → '.join(etiquetas)}")
        print(f"       Salida: {salida}")
        print()


def _continuar() -> bool:
    """Pregunta al usuario si desea buscar rutas desde otro nodo."""
    respuesta = input("  ¿Buscar rutas desde otra ubicación? (s/n): ").strip().lower()
    return respuesta == "s"