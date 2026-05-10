"""
infrastructure/visualization/cli_renderer.py

Renderizador de texto para resultados de simulación de evacuación múltiple.
Muestra en consola el avance paso a paso y el reporte final de congestiones.
"""

from application.simulate_evacuation import SimulationResult
from domain.graph import Graph


def render_simulation_steps(result: SimulationResult, graph: Graph) -> str:
    """
    Genera el log paso a paso de la simulación.

    Para cada paso muestra la posición de cada persona, señala congestiones
    y marca el momento exacto en que cada persona es evacuada.
    """
    if not result.steps:
        return "  (Sin pasos de simulación disponibles)"

    lines: list[str] = []

    for sim_step in result.steps:
        step_num = sim_step.step
        lines.append(f"  ┌── Paso {step_num} {'─' * 38}")

        for persona in result.personas:
            if persona.route is None:
                continue

            path = persona.route.path

            # Si ya evacuó antes de este paso, mostrar estado final
            if persona.evacuation_time is not None and step_num > persona.evacuation_time:
                lines.append(f"  │  [{persona.id}] {persona.name}: ✔ Ya evacuado")
                continue

            # Si el paso supera la ruta sin haber evacuado, omitir
            if step_num >= len(path):
                continue

            node_id = path[step_num]
            node_label = graph.get_node(node_id).label
            is_exit = graph.get_node(node_id).is_exit()
            congested = node_id in sim_step.congested_nodes

            if persona.id in sim_step.newly_evacuated:
                status = "  ✔ ¡EVACUADO!"
            elif congested:
                status = "  ⚠ CONGESTIÓN"
            else:
                status = ""

            exit_mark = " 🚪" if is_exit else ""
            lines.append(
                f"  │  [{persona.id}] {persona.name}: "
                f"{node_label} [{node_id}]{exit_mark}{status}"
            )

        lines.append("  │")

    return "\n".join(lines)


def render_simulation_summary(result: SimulationResult, graph: Graph) -> str:
    """
    Genera el reporte final de la simulación con:
    - Rutas asignadas y tiempos de evacuación por persona
    - Nodos con congestión (cuellos de botella)
    - Conexiones más transitadas
    - Personas sin ruta disponible
    """
    lines: list[str] = []

    lines.append("  ╔═══════════════════════════════════════════════════════╗")
    lines.append("  ║      REPORTE FINAL DE SIMULACIÓN DE EVACUACIÓN       ║")
    lines.append("  ╠═══════════════════════════════════════════════════════╣")

    # ── Personas y resultados individuales ───────────────────────────
    lines.append("  ║  PERSONAS Y RESULTADOS:                              ║")
    for persona in result.personas:
        if persona.route:
            if len(persona.route.path) <= 4:
                ruta_corta = " → ".join(persona.route.path)
            else:
                inicio = " → ".join(persona.route.path[:3])
                ruta_corta = f"{inicio} → ... ({len(persona.route.path) - 1} pasos)"

            if persona.evacuated:
                estado = f"✔ Evacuado en paso {persona.evacuation_time}"
            else:
                estado = "⏳ No completó evacuación"

            lines.append(f"  ║  [{persona.id}] {persona.name}: {estado}")
            lines.append(f"  ║      Ruta: {ruta_corta}")
        else:
            lines.append(f"  ║  [{persona.id}] {persona.name}: ✘ Sin ruta disponible")

    lines.append("  ╠═══════════════════════════════════════════════════════╣")

    # ── Cuellos de botella en nodos ───────────────────────────────────
    if result.congestion_nodes:
        lines.append("  ║  🚨 CUELLOS DE BOTELLA DETECTADOS (nodos):           ║")
        for node_id, peak in result.congestion_nodes:
            label = graph.get_node(node_id).label
            lines.append(f"  ║    • {label} [{node_id}]: pico de {peak} personas")
    else:
        lines.append("  ║  ✔ Sin cuellos de botella en nodos.                 ║")

    # ── Conexiones más transitadas ────────────────────────────────────
    if result.congestion_edges:
        lines.append("  ╠═══════════════════════════════════════════════════════╣")
        lines.append("  ║  🚨 CONEXIONES MÁS TRANSITADAS:                      ║")
        for (from_id, to_id), count in result.congestion_edges[:5]:
            fl = graph.get_node(from_id).label
            tl = graph.get_node(to_id).label
            lines.append(f"  ║    • {fl} → {tl}: {count} pases")

    lines.append("  ╠═══════════════════════════════════════════════════════╣")

    # ── Personas sin ruta ─────────────────────────────────────────────
    if result.unresolved:
        ids = ", ".join(result.unresolved)
        lines.append(f"  ║  ⚠ Sin ruta posible: {ids}")
        lines.append("  ╠═══════════════════════════════════════════════════════╣")

    # ── Totales ───────────────────────────────────────────────────────
    evacuados = sum(1 for p in result.personas if p.evacuated)
    total = len(result.personas)
    lines.append(f"  ║  Evacuados exitosamente: {evacuados}/{total} personas")
    lines.append(f"  ║  Duración total de simulación: {result.total_steps} pasos")
    lines.append("  ╚═══════════════════════════════════════════════════════╝")

    return "\n".join(lines)
