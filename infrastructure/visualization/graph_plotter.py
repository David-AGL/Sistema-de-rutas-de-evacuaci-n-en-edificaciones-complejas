"""
infrastructure/visualization/graph_plotter.py

Renderizado del mapa del edificio usando Graphviz.
Genera imágenes PNG para visualizar estructura, bloqueos y rutas recomendadas.
"""

from pathlib import Path
import os
import shutil

from domain.evacuation_state import EvacuationState
from domain.graph import Graph


def render_building_map(
	graph: Graph,
	state: EvacuationState,
	route: list[str] | None = None,
	title: str = "Mapa del edificio",
	output_dir: str = "output/maps",
	filename: str = "mapa_edificio",
) -> str:
	"""
	Renderiza el grafo del edificio en PNG usando Graphviz.

	Args:
		graph: grafo del edificio.
		state: estado dinámico de bloqueos.
		route: lista de IDs de la ruta a resaltar (opcional).
		title: título del diagrama.
		output_dir: carpeta de salida.
		filename: nombre base del archivo (sin extensión).

	Returns:
		Ruta absoluta al archivo PNG generado.

	Raises:
		RuntimeError: si falta el paquete graphviz de Python o el ejecutable de Graphviz.
	"""
	try:
		from graphviz import Graph as DotGraph
	except ImportError as exc:
		raise RuntimeError(
			"No se encontró el paquete 'graphviz'. Instala con: pip install graphviz"
		) from exc

	_ensure_dot_available()

	out_dir = Path(output_dir)
	out_dir.mkdir(parents=True, exist_ok=True)

	route_set = set(route or [])
	route_edges = _route_to_undirected_edges(route or [])

	dot = DotGraph(name="BuildingMap", format="png", engine="dot")
	dot.attr(label=title, labelloc="t", fontsize="18", fontname="Helvetica")
	dot.attr(rankdir="LR", splines="ortho", nodesep="0.55", ranksep="0.8")

	# Agrupar por piso para mejorar legibilidad.
	levels = sorted({node.level for node in graph.nodes.values()})
	for level in levels:
		with dot.subgraph(name=f"cluster_level_{level}") as sub:
			sub.attr(label=f"Piso {level}", color="#BDBDBD", style="rounded", penwidth="1.3")
			sub.attr(rank="same")

			level_nodes = sorted(
				[n for n in graph.nodes.values() if n.level == level],
				key=lambda n: n.id,
			)
			for node in level_nodes:
				attrs = _node_style(node.type)

				if node.id in state.blocked_nodes:
					attrs.update({"fillcolor": "#F8D7DA", "color": "#B00020", "penwidth": "2.2"})
				elif node.id in route_set:
					attrs.update({"fillcolor": "#FFF3CD", "color": "#B58900", "penwidth": "2.2"})

				label = f"{node.id}\\n{node.label}"
				sub.node(node.id, label=label, **attrs)

	seen_edges: set[tuple[str, str]] = set()
	for from_id, edges in graph.adjacency.items():
		for edge in edges:
			a, b = sorted((from_id, edge.to_id))
			edge_key = (a, b)
			if edge_key in seen_edges:
				continue
			seen_edges.add(edge_key)

			attrs = {"color": "#666666", "penwidth": "1.4"}
			if (a, b) in route_edges:
				attrs.update({"color": "#B58900", "penwidth": "2.8"})

			if state.is_edge_blocked(a, b) or edge.blocked:
				attrs.update({"color": "#B00020", "style": "dashed", "penwidth": "2.2", "label": "X"})

			dot.edge(a, b, **attrs)

	# Línea visual para conexiones verticales de escaleras entre pisos.
	for a, b in (("E1", "E1_2"), ("E2", "E2_2")):
		if a in graph.nodes and b in graph.nodes:
			dot.edge(a, b, color="#1F77B4", style="dotted", penwidth="1.8", constraint="false")

	output_base = out_dir / filename
	try:
		png_path = dot.render(filename=output_base.name, directory=str(out_dir), cleanup=True)
	except Exception as exc:
		raise RuntimeError(
			"No se pudo renderizar con Graphviz. Verifica que Graphviz esté instalado en el sistema y en PATH."
		) from exc

	return str(Path(png_path).resolve())


def _route_to_undirected_edges(route: list[str]) -> set[tuple[str, str]]:
	edges: set[tuple[str, str]] = set()
	for i in range(len(route) - 1):
		a, b = sorted((route[i], route[i + 1]))
		edges.add((a, b))
	return edges


def _node_style(node_type: str) -> dict[str, str]:
	base = {
		"style": "filled,rounded",
		"fillcolor": "#F5F5F5",
		"color": "#7A7A7A",
		"shape": "box",
		"fontname": "Helvetica",
		"fontsize": "10",
	}
	if node_type == "exit":
		base.update({"shape": "doublecircle", "fillcolor": "#D8F5D0", "color": "#2E7D32"})
	elif node_type == "hallway":
		base.update({"shape": "ellipse", "fillcolor": "#E8F0FE", "color": "#4E79A7"})
	elif node_type == "staircase":
		base.update({"shape": "box", "fillcolor": "#F0E5FF", "color": "#7E57C2"})
	return base


def _ensure_dot_available():
	"""Asegura que el ejecutable `dot` esté disponible para python-graphviz."""
	if shutil.which("dot"):
		return

	candidates = [
		"C:/Program Files/Graphviz/bin",
		"C:/Program Files (x86)/Graphviz/bin",
	]

	for cand in candidates:
		dot_path = Path(cand) / "dot.exe"
		if dot_path.exists():
			current_path = os.environ.get("PATH", "")
			os.environ["PATH"] = f"{cand}{os.pathsep}{current_path}" if current_path else cand
			if shutil.which("dot"):
				return

	raise RuntimeError(
		"No se encontró el ejecutable 'dot'. Instala Graphviz en el sistema y verifica PATH."
	)