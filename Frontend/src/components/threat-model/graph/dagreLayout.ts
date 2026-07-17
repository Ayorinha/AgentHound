import dagre from "@dagrejs/dagre";
import type { GraphEdge, GraphNode } from "@/types/ThreatModel";
import { nodeSize } from "@/components/threat-model/graph/cyberGraphTheme";

export function dagreLayout(
  nodes: GraphNode[],
  edges: GraphEdge[],
): Map<string, { x: number; y: number }> {
  const g = new dagre.graphlib.Graph();
  g.setGraph({
    rankdir: "LR",
    ranksep: 150,
    nodesep: 55,
    ranker: "network-simplex",
  });
  g.setDefaultEdgeLabel(() => ({}));

  for (const n of nodes) {
    const { w, h } = nodeSize(n.type);
    g.setNode(n.id, { width: w, height: h });
  }
  for (const e of edges) {
    g.setEdge(e.f, e.t);
  }

  dagre.layout(g);

  const pos = new Map<string, { x: number; y: number }>();
  for (const n of nodes) {
    const dn = g.node(n.id);
    // dagre positions are the node's center; React Flow expects top-left.
    if (dn) pos.set(n.id, { x: dn.x - dn.width / 2, y: dn.y - dn.height / 2 });
  }
  return pos;
}
