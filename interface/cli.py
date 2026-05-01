"""
interface/cli.py

Responsabilidad: interactuar con el usuario por consola.
  - Pide la ubicación de inicio
  - Permite bloquear nodos y aristas de forma interactiva
  - Llama al caso de uso FindRoutes con el estado actual
  - Muestra los resultados formateados

Lo que NO hace:
  - No implementa DFS
  - No modifica el grafo directamente
  - No tiene lógica de negocio
"""

from application.find_routes import FindRoutes
from application.block_path import block_node, unblock_node, block_edge, unblock_edge
from application.recommend_route import recommend_route, comparar_criterios, CRITERIOS_VALIDOS
from application.compare_routes import compare_routes, formato_tabla, formato_detalle
from domain.graph import Graph
from domain.evacuation_state import EvacuationState


def _safe_input(prompt: str) -> str | None:
    """Lee entrada y convierte Ctrl+C en cancelación limpia."""
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print("\n  Operación cancelada.")
        return None


def run_cli(graph: Graph, state: EvacuationState):
    """
    Punto de entrada de la interfaz de línea de comandos.

    Flujo dinámico:
      1. El usuario elige su ubicación.
      2. Entra en un menú persistente donde puede:
           - Ver rutas  (recalculadas en tiempo real con el estado actual)
           - Bloquear nodo / arista
           - Desbloquear nodo / arista
           - Cambiar de ubicación
           - Resetear todos los bloqueos
           - Salir
      Cada vez que se muestra el menú, se imprime el estado actual
      de bloqueos para que el usuario siempre sepa qué está activo.
    """
    _print_header(graph)

    # Paso 1: elegir ubicación inicial
    start = _pedir_ubicacion(graph, state)
    if start is None:
        print("\n  Cerrando sistema de evacuación. ¡Mantén la calma!\n")
        return

    # Paso 2: ciclo dinámico principal
    while True:
        _print_menu(graph, state, start)
        opcion_raw = _safe_input("  Opción: ")
        if opcion_raw is None:
            continue
        opcion = opcion_raw.strip()

        if opcion == "1":
            # Recalcular y mostrar rutas con el estado actual
            _buscar_y_mostrar(graph, state, start)

        elif opcion == "2":
            while True:
                nodo_id = input("  ID del nodo a bloquear (o Enter para cancelar): ").strip()
                if nodo_id == "":
                    break
                try:
                    block_node(graph, state, nodo_id)
                    print(f"  ✔ '{nodo_id}' bloqueado. Recalcula rutas para ver el impacto.")
                    break
                except (KeyError, ValueError) as e:
                    print(f"  ✘ Error: {e}")
                    print("  Intenta de nuevo o presiona Enter para cancelar:")

        elif opcion == "3":
            while True:
                desde = input("  ID del nodo origen de la conexión (o Enter para cancelar): ").strip()
                if desde == "":
                    break
                hasta = input("  ID del nodo destino de la conexión (o Enter para cancelar): ").strip()
                if hasta == "":
                    break
                try:
                    block_edge(graph, state, desde, hasta)
                    print(f"  ✔ Conexión '{desde}' ↔ '{hasta}' bloqueada.")
                    break
                except (KeyError, ValueError) as e:
                    print(f"  ✘ Error: {e}")
                    print("  Intenta de nuevo o presiona Enter para cancelar:")

        elif opcion == "4":
            while True:
                nodo_id = input("  ID del nodo a desbloquear (o Enter para cancelar): ").strip()
                if nodo_id == "":
                    break
                try:
                    unblock_node(graph, state, nodo_id)
                    print(f"  ✔ '{nodo_id}' desbloqueado.")
                    break
                except KeyError as e:
                    print(f"  ✘ Error: {e}")
                    print("  Intenta de nuevo o presiona Enter para cancelar:")

        elif opcion == "5":
            while True:
                desde = input("  ID del nodo origen de la conexión (o Enter para cancelar): ").strip()
                if desde == "":
                    break
                hasta = input("  ID del nodo destino de la conexión (o Enter para cancelar): ").strip()
                if hasta == "":
                    break
                try:
                    unblock_edge(graph, state, desde, hasta)
                    print(f"  ✔ Conexión '{desde}' ↔ '{hasta}' desbloqueada.")
                    break
                except (KeyError, ValueError) as e:
                    print(f"  ✘ Error: {e}")
                    print("  Intenta de nuevo o presiona Enter para cancelar:")

        elif opcion == "6":
            # Cambiar de ubicación sin perder los bloqueos activos
            nueva = _pedir_ubicacion(graph, state)
            if nueva is not None:
                start = nueva

        elif opcion == "7":
            if state.has_blocks():
                state.reset()
                print("  ✔ Todos los bloqueos eliminados.")
            else:
                print("  No había bloqueos activos.")

        elif opcion == "8":
            _recomendar_ruta(graph, state, start)

        elif opcion == "9":
            _comparar_rutas(graph, state, start)

        elif opcion == "0":
            break

        else:
            print("  ✘ Opción inválida.")

    print("\n  Cerrando sistema de evacuación. ¡Mantén la calma!\n")


# ------------------------------------------------------------------ #
# Sección: cabecera                                                   #
# ------------------------------------------------------------------ #

def _print_header(graph: Graph):
    salidas = [n.label for n in graph.get_exits()]
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║       SISTEMA DE RUTAS DE EVACUACIÓN                ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"  ✔ Edificio cargado: {len(graph.nodes)} nodos, {sum(len(v) for v in graph.adjacency.values()) // 2} conexiones")
    print(f"  Salidas registradas: {', '.join(salidas)}")
    print()
    _mostrar_nodos_disponibles(graph)
    print()


def _mostrar_nodos_disponibles(graph: Graph):
    print()
    print("  Nodos disponibles:")
    por_piso: dict[int, list] = {}
    for node in graph.nodes.values():
        por_piso.setdefault(node.level, []).append(node)

    iconos = {"room": "•", "hallway": "•", "staircase": "•", "exit": "•"}

    for nivel in sorted(por_piso):
        print(f"  Piso {nivel}:")
        for node in por_piso[nivel]:
            icono = iconos.get(node.type, "•")
            print(f"    {icono}  [{node.id:<6}]  {node.label}")
    print()


# ------------------------------------------------------------------ #
# Sección: ubicación inicial                                          #
# ------------------------------------------------------------------ #

def _pedir_ubicacion(graph: Graph, state: EvacuationState) -> str | None:
    while True:
        print()
        entrada_raw = _safe_input("  Ingrese su ubicación actual (ID del nodo) o 'salir': ")
        if entrada_raw is None:
            continue
        entrada = entrada_raw.strip()

        if entrada.lower() == "salir":
            return None

        if entrada not in graph.nodes:
            print(f"  ✘ '{entrada}' no existe en el edificio. Intente de nuevo.")
            continue

        if state.is_node_blocked(entrada):
            print(f"  ✘ '{entrada}' está bloqueado. Elija otra ubicación.")
            continue

        nodo = graph.get_node(entrada)
        print(f"  ✔ Ubicación confirmada: {nodo.label} (Piso {nodo.level})")
        return entrada


# ------------------------------------------------------------------ #
# Sección: menú dinámico                                              #
# ------------------------------------------------------------------ #

def _print_menu(graph: Graph, state: EvacuationState, start_id: str):
    """
    Imprime el menú principal con el contexto actual visible:
    ubicación activa y bloqueos registrados.
    El usuario siempre sabe en qué estado está el sistema.
    """
    nodo = graph.get_node(start_id)
    print()
    print("  ══════════════════════════════════════════════════")
    print(f"  📍 {nodo.label} [{start_id}] | Piso {nodo.level}")

    if state.has_blocks():
        print("  🚧 Bloqueos activos:")
        for line in state.summary().splitlines():
            print(f"     {line.strip()}")
    else:
        print("  🟢 Sin bloqueos activos")

    print("  ══════════════════════════════════════════════════")
    print("    ➤ [1] Ver rutas de evacuación")
    print("      [2] Bloquear nodo")
    print("      [3] Bloquear conexión (arista)")
    print("      [4] Desbloquear nodo")
    print("      [5] Desbloquear conexión (arista)")
    print("      [6] Cambiar ubicación")
    print("      [7] Resetear todos los bloqueos")
    print("      [8] Recomendar mejor ruta")
    print("      [9] Comparar rutas con métricas")
    print("      [0] Salir")
    print()


# ------------------------------------------------------------------ #
# Sección: búsqueda y resultados                                      #
# ------------------------------------------------------------------ #

def _buscar_y_mostrar(graph: Graph, state: EvacuationState, start_id: str):
    """Llama a FindRoutes con el estado actual y muestra los resultados."""
    finder = FindRoutes(graph, state)
    routes = finder.find_all(start_id)

    print()
    print("  ┌─────────────────────────────────────────────────┐")

    if not routes:
        print("  │  ✘ No hay rutas disponibles desde esta ubicación.")
        print("  │    Revise los bloqueos activos.")
        print("  └─────────────────────────────────────────────────┘")
        return

    print(f"  │  Se encontraron {len(routes)} ruta(s) de evacuación:")
    print("  └─────────────────────────────────────────────────┘")
    print()

    for i, route in enumerate(routes, 1):
        etiquetas = [graph.get_node(nid).label for nid in route.path]
        ruta_ids  = _formatear_ruta_multilinea(route.path)
        salida    = graph.get_node(route.exit_id).label
        prefijo   = "  ★ " if i == 1 else f"  {i}.  "
        nota      = "  ← MEJOR RUTA" if i == 1 else ""

        print(f"{prefijo}[Costo: {route.cost:>3}]  {ruta_ids}{nota}")
        print(f"       Descripción: {' → '.join(etiquetas)}")
        print(f"       Salida: {salida}")
        print()


# ------------------------------------------------------------------ #
# Sección: recomendación de mejor ruta                                #
# ------------------------------------------------------------------ #

def _recomendar_ruta(graph: Graph, state: EvacuationState, start_id: str):
    """
    Calcula todas las rutas disponibles, las muestra y destaca
    la mejor según el criterio que elija el usuario.
    """
    routes = FindRoutes(graph, state).find_all(start_id)

    print()
    if not routes:
        print("  ✘ No hay rutas disponibles. No se puede recomendar.")
        return

    # Mostrar todas las rutas primero como contexto
    print(f"  Rutas disponibles desde [{start_id}] ({len(routes)} total):")
    print()
    for i, r in enumerate(routes, 1):
        ids = " → ".join(r.path)
        print(f"    {i}. [Costo {r.cost:>2} | {len(r.path)-1} pasos]  {ids}")

    # Pedir criterio de recomendación con descripciones
    print()
    print("  Criterios disponibles:")
    print("    - costo  → Ruta más corta (menor costo total)")
    print("    - pasos  → Menor número de tramos")
    print("    - mixto  → Balance entre costo y pasos (recomendado)")
    print()

    # Reintentar si el input es inválido
    while True:
        criterio_raw = _safe_input("  ¿Con qué criterio recomendar? (Enter = 'costo'): ")
        if criterio_raw is None:
            return
        criterio = criterio_raw.strip().lower()
        if criterio == "":
            criterio = "costo"

        try:
            mejor = recommend_route(routes, criterio)
            break  # Si es válido, salir del loop
        except ValueError as e:
            print(f"  ✘ {e}")
            print("  Intenta de nuevo:")
            continue

    # Mostrar la recomendación destacada
    print()
    print("  ╔═══════════════════════════════════════════════════════╗")
    print(f"  ║  ★ RUTA RECOMENDADA (criterio: {criterio.upper():<20})  ║")
    print("  ╠═══════════════════════════════════════════════════════╣")
    ids_str = _formatear_ruta_multilinea(mejor.path, ancho=43)
    print(f"  ║  Ruta   : {ids_str}")
    etiquetas = [graph.get_node(nid).label for nid in mejor.path]
    det_str = _formatear_ruta_multilinea(etiquetas, ancho=43)
    print(f"  ║  Detalle: {det_str}")
    print(f"  ║  Costo  : {mejor.cost:>3}   |   Pasos: {len(mejor.path) - 1:<2}")
    print(f"  ║  Salida : {graph.get_node(mejor.exit_id).label}")
    print("  ╚═══════════════════════════════════════════════════════╝")

    # Si hay más de una ruta, mostrar comparación entre criterios
    if len(routes) > 1:
        comparacion = comparar_criterios(routes)
        print()
        print("  Comparación entre criterios:")
        for crit, ruta in comparacion.items():
            ids  = _formatear_ruta_multilinea(ruta.path, ancho=43)
            mark = "  ★ ← ELEGIDO" if crit == criterio else ""
            print(f"    {crit:<6}: [Costo {ruta.cost:>2} | {len(ruta.path)-1} pasos]  {ids}{mark}")

# ------------------------------------------------------------------ #
# Sección: comparación de rutas con métricas                          #
# ------------------------------------------------------------------ #

def _comparar_rutas(graph: Graph, state: EvacuationState, start_id: str):
    """
    Muestra la tabla comparativa de todas las rutas disponibles
    y permite ver el detalle completo de cualquiera de ellas.
    """
    routes = FindRoutes(graph, state).find_all(start_id)

    print()
    if not routes:
        print("  ✘ No hay rutas disponibles para comparar.")
        return

    metricas = compare_routes(routes, graph)

    # ── Vista principal: tabla comparativa ───────────────────────────
    print("  COMPARACIÓN DE RUTAS DE EVACUACIÓN")
    print()
    print(formato_tabla(metricas))

    # ── Leyenda de columnas ───────────────────────────────────────────
    print()
    print("  Columnas: Costo=suma de pesos  |  Pasos=tramos recorridos  "
          "|  Escal.=escaleras  |  Efic.=costo/paso")

    if len(metricas) == 1:
        return

    # ── Vista detalle: el usuario elige una ruta para ampliar ────────
    print()
    while True:
        seleccion_raw = _safe_input(
            f"  Ver detalle de una ruta (1-{len(metricas)}) o Enter para volver: "
        )
        if seleccion_raw is None:
            return
        seleccion = seleccion_raw.strip()

        if seleccion == "":
            return

        try:
            idx = int(seleccion)
            if not (1 <= idx <= len(metricas)):
                raise ValueError
            break  # Selección válida, salir del loop
        except ValueError:
            print(f"  ✘ Ingresa un número entre 1 y {len(metricas)}, o presiona Enter.")
            continue

    print()
    print(formato_detalle(metricas[idx - 1]))


def _formatear_ruta_multilinea(partes: list[str], ancho: int = 44) -> str:
    """Divide una ruta larga en varias líneas para mejorar la lectura."""
    if not partes:
        return ""

    texto = " → ".join(partes)
    if len(texto) <= ancho:
        return texto

    lineas = []
    actual = partes[0]
    for parte in partes[1:]:
        candidato = f"{actual} → {parte}"
        if len(candidato) <= ancho:
            actual = candidato
        else:
            lineas.append(actual)
            actual = f"→ {parte}"
    lineas.append(actual)
    return "\n       ".join(lineas)