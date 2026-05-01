"""
infrastructure/persistence/building_loader.py

Responsabilidad: leer el archivo JSON del edificio y convertirlo
en un objeto Graph listo para usar.

Esta capa "infraestructura" es la única que sabe que los datos
vienen de un archivo JSON. El resto del sistema solo trabaja con Graph.
"""

import json
from pathlib import Path

from domain.node import Node
from domain.edge import Edge
from domain.graph import Graph


class BuildingLoader:
    """
    Lee un archivo building.json y construye el grafo del edificio.

    Uso:
        loader = BuildingLoader("data/building.json")
        graph  = loader.load()
    """

    def __init__(self, filepath: str):
        """
        Args:
            filepath: Ruta al archivo JSON del edificio.
                      Puede ser relativa o absoluta.
        """
        self.filepath = Path(filepath)

    # ------------------------------------------------------------------ #
    # Método principal                                                     #
    # ------------------------------------------------------------------ #

    def load(self) -> Graph:
        """
        Lee el JSON, construye y retorna el grafo del edificio.

        Returns:
            Graph con todos los nodos y aristas cargados.

        Raises:
            FileNotFoundError: Si el archivo no existe.
            KeyError:          Si el JSON tiene campos faltantes.
            ValueError:        Si algún dato tiene un valor inválido.
        """
        raw = self._read_file()
        graph = Graph()

        self._load_nodes(raw, graph)
        self._load_edges(raw, graph)

        return graph

    # ------------------------------------------------------------------ #
    # Pasos internos                                                       #
    # ------------------------------------------------------------------ #

    def _read_file(self) -> dict:
        """Lee y parsea el archivo JSON."""
        if not self.filepath.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo del edificio: '{self.filepath}'"
            )

        with open(self.filepath, encoding="utf-8") as f:
            return json.load(f)

    def _load_nodes(self, raw: dict, graph: Graph):
        """
        Recorre la lista 'nodes' del JSON y agrega cada uno al grafo.

        Formato esperado de cada nodo en el JSON:
            {
                "id":    "A101",
                "label": "Aula 101",
                "type":  "room",
                "level": 1
            }
        """
        nodes_data = raw.get("nodes", [])

        if not nodes_data:
            raise ValueError("El JSON no contiene nodos ('nodes' vacío o ausente).")

        for item in nodes_data:
            node = Node(
                node_id=item["id"],
                label=item["label"],
                node_type=item["type"],
                level=item["level"]
            )
            graph.add_node(node)

    def _load_edges(self, raw: dict, graph: Graph):
        """
        Recorre la lista 'edges' del JSON y agrega cada arista al grafo.

        Formato esperado de cada arista en el JSON:
            {
                "from":        "A101",
                "to":          "P1N",
                "weight":      1,
                "description": "Puerta Aula 101 al pasillo norte"
            }
        """
        edges_data = raw.get("edges", [])

        if not edges_data:
            raise ValueError("El JSON no contiene aristas ('edges' vacío o ausente).")

        for item in edges_data:
            # Verificar que los nodos referenciados existan en el grafo
            from_id = item["from"]
            to_id   = item["to"]

            if from_id not in graph.nodes:
                raise KeyError(
                    f"Arista inválida: el nodo origen '{from_id}' no existe en el grafo."
                )
            if to_id not in graph.nodes:
                raise KeyError(
                    f"Arista inválida: el nodo destino '{to_id}' no existe en el grafo."
                )

            edge = Edge(
                from_id=from_id,
                to_id=to_id,
                weight=item.get("weight", 1),
                description=item.get("description", "")
            )
            graph.add_edge(edge)
