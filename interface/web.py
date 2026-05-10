"""
interface/web.py

Interfaz web del sistema de evacuación (Flask).
Envuelve los casos de uso existentes en endpoints HTTP/JSON.
Estado global de un solo usuario (demo académico).
"""

import json
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_file

from infrastructure.persistence.building_loader import BuildingLoader
from domain.evacuation_state import EvacuationState
from application.find_routes import FindRoutes
from application.block_path import (
    block_node as _block_node, unblock_node as _unblock_node,
    block_edge as _block_edge, unblock_edge as _unblock_edge,
)
from application.recommend_route import recommend_route, comparar_criterios
from application.compare_routes import compare_routes
from application.simulate_evacuation import SimulateEvacuation
from application.emergency_mode import apply_emergency_blockages, INTENSIDADES
from infrastructure.visualization.graph_plotter import render_building_map

app = Flask(__name__, template_folder='../templates', static_folder='../static')

_graph = None
_state = None


# ── helpers ───────────────────────────────────────────────────────────

def _n(nid):
    node = _graph.get_node(nid)
    return {
        'id': node.id, 'label': node.label,
        'type': node.type, 'level': node.level,
        'is_exit': node.is_exit(),
        'blocked': _state.is_node_blocked(nid),
    }

def _unique_edges():
    seen, result = set(), []
    for nid, adj in _graph.adjacency.items():
        for e in adj:
            key = (min(e.from_id, e.to_id), max(e.from_id, e.to_id))
            if key in seen:
                continue
            seen.add(key)
            result.append({
                'from': e.from_id, 'to': e.to_id,
                'from_label': _graph.get_node(e.from_id).label,
                'to_label': _graph.get_node(e.to_id).label,
                'weight': e.weight,
                'blocked': _state.is_edge_blocked(e.from_id, e.to_id),
            })
    return result


# ── vistas ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ── edificios ─────────────────────────────────────────────────────────

@app.route('/api/buildings')
def api_buildings():
    result = []
    for path in sorted(Path('data').glob('*.json')):
        try:
            d = json.loads(path.read_text(encoding='utf-8'))
            name   = d.get('building', {}).get('name', path.stem)
            levels = d.get('building', {}).get('levels', 1)
        except Exception:
            name, levels = path.stem, 1
        result.append({'path': str(path), 'name': name, 'levels': levels})
    return jsonify(result)


@app.route('/api/load', methods=['POST'])
def api_load():
    global _graph, _state
    d = request.json
    try:
        _graph = BuildingLoader(d['path']).load()
        _state = EvacuationState()
        emergency = None
        if d.get('mode') == 'emergencia':
            blocked = apply_emergency_blockages(_graph, _state, d.get('intensity', 'moderada'))
            emergency = {
                'nodos':   [_n(nid) for nid in blocked['nodos']],
                'aristas': [
                    {'from': f, 'to': t,
                     'from_label': _graph.get_node(f).label,
                     'to_label':   _graph.get_node(t).label}
                    for (f, t) in blocked['aristas']
                ],
            }
        return jsonify({
            'ok': True,
            'node_count': len(_graph.nodes),
            'exits': [_n(n.id) for n in _graph.get_exits()],
            'emergency': emergency,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/nodes')
def api_nodes():
    if _graph is None:
        return jsonify([])
    return jsonify([_n(nid) for nid in _graph.nodes])


@app.route('/api/edges')
def api_edges():
    if _graph is None:
        return jsonify([])
    return jsonify(_unique_edges())


@app.route('/api/state')
def api_state():
    if _state is None:
        return jsonify({'blocked_nodes': [], 'blocked_edges': []})
    return jsonify({
        'blocked_nodes': [
            {'id': nid, 'label': _graph.get_node(nid).label}
            for nid in _state.blocked_nodes if nid in _graph.nodes
        ],
        'blocked_edges': [
            {'from': a, 'to': b,
             'from_label': _graph.get_node(a).label,
             'to_label':   _graph.get_node(b).label}
            for (a, b) in _state.blocked_edges
            if a < b and a in _graph.nodes and b in _graph.nodes
        ],
    })


# ── rutas ─────────────────────────────────────────────────────────────

@app.route('/api/routes', methods=['POST'])
def api_routes():
    if _graph is None:
        return jsonify({'error': 'Sin edificio'}), 400
    start = request.json.get('start_id')
    routes = FindRoutes(_graph, _state).find_all(start)
    return jsonify({'routes': [
        {
            'rank': i + 1,
            'path': r.path,
            'nodes': [_n(nid) for nid in r.path],
            'cost': r.cost,
            'steps': len(r.path) - 1,
            'exit_label': _graph.get_node(r.exit_id).label,
        }
        for i, r in enumerate(routes)
    ]})


@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    if _graph is None:
        return jsonify({'error': 'Sin edificio'}), 400
    d = request.json
    routes = FindRoutes(_graph, _state).find_all(d.get('start_id'))
    if not routes:
        return jsonify({'error': 'Sin rutas disponibles'}), 400
    criterio = d.get('criterio', 'costo')
    best = recommend_route(routes, criterio)
    comp = comparar_criterios(routes) if len(routes) > 1 else {}
    return jsonify({
        'route': {
            'path': best.path,
            'nodes': [_n(nid) for nid in best.path],
            'cost': best.cost,
            'steps': len(best.path) - 1,
            'exit_label': _graph.get_node(best.exit_id).label,
        },
        'criterio': criterio,
        'comparacion': {
            c: {'path': r.path, 'cost': r.cost, 'steps': len(r.path) - 1}
            for c, r in comp.items()
        },
    })


@app.route('/api/compare', methods=['POST'])
def api_compare():
    if _graph is None:
        return jsonify({'error': 'Sin edificio'}), 400
    start = request.json.get('start_id')
    routes = FindRoutes(_graph, _state).find_all(start)
    metricas = compare_routes(routes, _graph)
    return jsonify({'routes': [
        {
            'rank': m.rank,
            'path': m.route.path,
            'etiquetas': m.etiquetas,
            'costo': m.costo,
            'pasos': m.pasos,
            'n_escaleras': m.n_escaleras,
            'n_pasillos': m.n_pasillos,
            'salida': m.salida_label,
            'eficiencia': m.eficiencia,
        }
        for m in metricas
    ]})


# ── bloqueos ──────────────────────────────────────────────────────────

@app.route('/api/block/node', methods=['POST'])
def api_block_node():
    try:
        _block_node(_graph, _state, request.json['node_id'])
        return jsonify({'ok': True})
    except (KeyError, ValueError) as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/unblock/node', methods=['POST'])
def api_unblock_node():
    try:
        _unblock_node(_graph, _state, request.json['node_id'])
        return jsonify({'ok': True})
    except KeyError as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/block/edge', methods=['POST'])
def api_block_edge():
    d = request.json
    try:
        _block_edge(_graph, _state, d['from_id'], d['to_id'])
        return jsonify({'ok': True})
    except (KeyError, ValueError) as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/unblock/edge', methods=['POST'])
def api_unblock_edge():
    d = request.json
    try:
        _unblock_edge(_graph, _state, d['from_id'], d['to_id'])
        return jsonify({'ok': True})
    except (KeyError, ValueError) as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/reset', methods=['POST'])
def api_reset():
    if _state:
        _state.reset()
    return jsonify({'ok': True})


# ── mapa ──────────────────────────────────────────────────────────────

@app.route('/api/map', methods=['POST'])
def api_map():
    if _graph is None:
        return jsonify({'error': 'Sin edificio'}), 400
    d = request.json or {}
    try:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S%f')
        png_path = render_building_map(
            graph=_graph, state=_state,
            route=d.get('route'),
            title=d.get('title', 'Mapa del Edificio'),
            output_dir='output/maps',
            filename=f'web_{ts}',
        )
        return send_file(str(Path(png_path).resolve()), mimetype='image/png')
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500


# ── simulación ────────────────────────────────────────────────────────

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    if _graph is None:
        return jsonify({'error': 'Sin edificio'}), 400
    d = request.json
    personas = d.get('personas', [])
    if not personas:
        return jsonify({'error': 'Sin personas'}), 400

    sim = SimulateEvacuation(_graph, _state)
    for p in personas:
        sim.add_person(p['id'], p['name'], p['start_id'])

    result = sim.run(criterio=d.get('criterio', 'costo'))
    return jsonify({
        'personas': [
            {
                'id': p.id, 'name': p.name, 'start_id': p.start_id,
                'route_labels': [_graph.get_node(nid).label for nid in p.route.path] if p.route else None,
                'evacuated': p.evacuated,
                'evacuation_time': p.evacuation_time,
            }
            for p in result.personas
        ],
        'steps': [
            {
                'step': s.step,
                'positions': {
                    pid: {
                        'node_id': nid,
                        'label': _graph.get_node(nid).label,
                        'is_exit': _graph.get_node(nid).is_exit(),
                    }
                    for pid, nid in s.positions.items()
                },
                'congested_nodes': s.congested_nodes,
                'newly_evacuated': s.newly_evacuated,
            }
            for s in result.steps
        ],
        'congestion_nodes': [
            {'id': nid, 'label': _graph.get_node(nid).label, 'peak': peak}
            for nid, peak in result.congestion_nodes
        ],
        'congestion_edges': [
            {'from_label': _graph.get_node(f).label,
             'to_label': _graph.get_node(t).label, 'count': c}
            for (f, t), c in result.congestion_edges
        ],
        'total_steps': result.total_steps,
        'unresolved': result.unresolved,
    })
