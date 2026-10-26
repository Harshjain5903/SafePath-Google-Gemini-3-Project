"""
Tests for RoutingEngine endpoint snapping, using a tiny synthetic street graph
instead of the full Chicago network.
"""
import sys
from pathlib import Path

import networkx as nx
import osmnx as ox
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "risk_aware_routing"))
from routing_engine import RoutingEngine  # noqa: E402


@pytest.fixture
def engine(tmp_path):
    """
    A <-> B <-> D is a two-way street. C is a one-way dead end that only
    leads OUT to B (C -> B), so nothing can route INTO C.
    """
    G = nx.MultiDiGraph(crs="epsg:4326")
    nodes = {1: (41.880, -87.630), 2: (41.881, -87.630), 3: (41.8815, -87.6290), 4: (41.882, -87.630)}
    for n, (lat, lng) in nodes.items():
        G.add_node(n, y=lat, x=lng)
    for u, v in [(1, 2), (2, 1), (2, 4), (4, 2), (3, 2)]:
        G.add_edge(u, v, length=100.0, travel_time=10.0)

    path = tmp_path / "graph.graphml"
    ox.save_graphml(G, path)
    return RoutingEngine(cache_path=str(path))


def test_dead_end_node_excluded_from_snapping(engine):
    assert 3 in engine.G
    assert 3 not in engine.G_snap


def test_route_to_point_near_unreachable_node(engine):
    # Destination is right on top of C (the one-way dead end)
    route = engine.get_route([41.880, -87.630], [41.8815, -87.6290])
    assert route[0] == [41.880, -87.630]
    assert route[-1] != [41.8815, -87.6290]  # snapped to a reachable node instead


def test_route_between_connected_nodes(engine):
    route = engine.get_route([41.880, -87.630], [41.882, -87.630])
    assert route == [[41.880, -87.630], [41.881, -87.630], [41.882, -87.630]]
