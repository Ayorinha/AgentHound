"""Build a networkx.MultiDiGraph from the IR (spec section 9).

Each node stores ``type``, ``name`` and ``properties``; each edge stores
``edge_id``, ``capability`` and ``properties``. A MultiDiGraph is used because
two nodes may be connected by more than one capability.
"""

from __future__ import annotations

from collections.abc import Iterable

import networkx as nx

from ..ir.models import AnalysisIR


def build_graph(ir: AnalysisIR, excluded_edge_ids: Iterable[str] | None = None) -> nx.MultiDiGraph:
    """Build the capability graph, optionally omitting some edges.

    ``excluded_edge_ids`` lets the control simulator (spec section 11) recompute
    rules over a graph in which blocked (``effect: total``) hops have been cut,
    without mutating the stored IR.
    """
    excluded = set(excluded_edge_ids or ())
    graph: nx.MultiDiGraph = nx.MultiDiGraph()
    for node in ir.nodes:
        graph.add_node(
            node.id,
            type=node.type.value,
            name=node.name,
            properties=node.properties,
        )
    for edge in ir.edges:
        if edge.id in excluded:
            continue
        # Skip edges whose endpoints are absent so the graph stays consistent;
        # validators run before this and would have already rejected such IR.
        if edge.source in graph and edge.target in graph:
            graph.add_edge(
                edge.source,
                edge.target,
                key=edge.id,
                edge_id=edge.id,
                capability=edge.capability,
                properties=edge.properties,
            )
    return graph
