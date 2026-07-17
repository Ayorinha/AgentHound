import ELK from "elkjs/lib/elk.bundled.js";
import type { GraphEdge, GraphNode } from "@/types/ThreatModel";
import { nodeSize } from "@/components/threat-model/graph/cyberGraphTheme";

const elk = new ELK();

/**
 * Runs an ELK `layered` layout (the approach React Flow's official elkjs
 * example uses) and returns top-left positions per node id. Curved edges are
 * still drawn by React Flow; ELK only decides positions. Nodes are layered by
 * dependency (not by type) so the flow reads left→right with minimal crossings —
 * node type stays legible through colour and the kicker label.
 */
export async function elkLayout(
  nodes: GraphNode[],
  edges: GraphEdge[],
): Promise<Map<string, { x: number; y: number }>> {
  const graph = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.layered.spacing.nodeNodeBetweenLayers": "150",
      "elk.spacing.nodeNode": "55",
      "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
      "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
      "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
      "elk.layered.cycleBreaking.strategy": "DEPTH_FIRST",
    },
    children: nodes.map((n) => {
      const { w, h } = nodeSize(n.type);
      return { id: n.id, width: w, height: h };
    }),
    edges: edges.map((e) => ({ id: e.id, sources: [e.f], targets: [e.t] })),
  };

  const res = await elk.layout(graph);
  const pos = new Map<string, { x: number; y: number }>();
  for (const c of res.children ?? []) {
    if (typeof c.x === "number" && typeof c.y === "number") pos.set(c.id, { x: c.x, y: c.y });
  }
  return pos;
}
