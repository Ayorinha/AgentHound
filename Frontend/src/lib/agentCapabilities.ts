import type { GraphEdge, GraphNode } from "@/types/ThreatModel";

export interface CapabilityLink {
  edge: GraphEdge;
  node: GraphNode;
}

export interface AgentCapabilities {
  agent: GraphNode;
  receivesFrom: CapabilityLink[];
  usesTools: CapabilityLink[];
  dataAccess: CapabilityLink[];
  memoryAccess: CapabilityLink[];
  delegatesTo: CapabilityLink[];
  sendsTo: CapabilityLink[];
  other: CapabilityLink[];
}

/** The capability rows a user can correct inside an agent's own card. `other`
 * is a display-only fallback bucket (unexpected target types) and isn't editable. */
export type EditableCapabilityRow =
  | "receivesFrom"
  | "usesTools"
  | "dataAccess"
  | "memoryAccess"
  | "delegatesTo"
  | "sendsTo";

/** For each editable row: the type of node created when adding a new entry
 * (matching node_properties.yaml's node_types), the edge direction relative to
 * the agent, and the default capability verb from capabilities.yaml. */
export const ROW_CONFIG: Record<
  EditableCapabilityRow,
  { nodeType: GraphNode["type"]; direction: "in" | "out"; defaultCapability: string }
> = {
  receivesFrom: { nodeType: "input", direction: "in", defaultCapability: "receiveInstruction" },
  usesTools: { nodeType: "tool", direction: "out", defaultCapability: "invokeTool" },
  dataAccess: { nodeType: "data", direction: "out", defaultCapability: "read" },
  memoryAccess: { nodeType: "memory", direction: "out", defaultCapability: "readMemory" },
  delegatesTo: { nodeType: "agent", direction: "out", defaultCapability: "delegateTo" },
  sendsTo: { nodeType: "output", direction: "out", defaultCapability: "send" },
};

/** The editable rows in the order they should be shown in the card and the
 * edit modal. `other` is intentionally excluded — it is a display-only bucket. */
export const EDITABLE_ROWS: EditableCapabilityRow[] = [
  "receivesFrom",
  "usesTools",
  "dataAccess",
  "memoryAccess",
  "delegatesTo",
  "sendsTo",
];

/**
 * Catalog of neutral capability verbs offered per row inside the agent edit
 * modal, grouped by the row (target type) they attach to. Mirrors the neutral
 * verbs in Backend/app/catalogs/capabilities.yaml, grouped by each verb's
 * `typical_target`. Internal-only capabilities (plan, decide, infer,
 * prioritize, resolveConflict, handleError) produce no graph edges and are
 * omitted here; they live in the backend YAML only.
 */
export const CAPABILITY_CATALOG: Record<EditableCapabilityRow, string[]> = {
  // input → agent
  receivesFrom: ["receiveInstruction", "receiveEvent", "interpretIntent"],

  // agent → tool
  usesTools: [
    "invokeTool",
    "executeCode",
    "observeState",
    "authenticate",
    "authorize",
    "verifyResult",
    "retry",
    "rollback",
    "deployRelease",
    "detectRisk",
  ],

  // agent → data_asset
  dataAccess: [
    "read",
    "fetchWeb",
    "search",
    "extractInformation",
    "classify",
    "summarize",
    "validate",
    "rewrite",
    "translate",
    "convertFormat",
    "normalizeData",
    "enrichData",
    "generateContent",
    "moveResource",
    "protectInformation",
  ],

  // agent → memory
  memoryAccess: ["readMemory", "writeMemory", "updateContext", "forgetContext", "manageWorkflowState"],

  // agent → agent
  delegatesTo: ["delegateTo", "dataFlow"],

  // agent → output
  sendsTo: [
    "send",
    "createResource",
    "modifyResource",
    "deleteResource",
    "respondUser",
    "notify",
    "requestInformation",
    "requestConfirmation",
    "escalate",
    "auditLog",
    "recordProgress",
    "finalizeTask",
  ],
};

export interface AgentCapabilityModel {
  agents: AgentCapabilities[];
  /** Nodes not reachable from any agent — shared/global elements, never controls. */
  unassigned: GraphNode[];
}

/**
 * Groups the backend-inferred graph by agent, mirroring how the source YAML
 * actually nests inputs/tools/data under each agent (see e.g.
 * fixture_crewai_risky_agents.yaml). Grouping is driven purely by edge
 * direction + the connected node's type, using the neutral capability verbs
 * from Backend/app/catalogs/capabilities.yaml (receiveInstruction, read,
 * fetchWeb, send, delegateTo, readMemory/writeMemory, invokeTool, ...) — no
 * capability names or relationships are invented here.
 *
 * `control` nodes are dropped: node_properties.yaml defaults every control to
 * status "absent" because a control is a recommendation the analysis produces,
 * not a fact extracted from the YAML. Controls belong in the Results step.
 */
export function groupByAgent(nodes: GraphNode[], edges: GraphEdge[]): AgentCapabilityModel {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const touchedIds = new Set<string>();

  const agents: AgentCapabilities[] = nodes
    .filter((n) => n.type === "agent")
    .map((agent) => {
      touchedIds.add(agent.id);
      const group: AgentCapabilities = {
        agent,
        receivesFrom: [],
        usesTools: [],
        dataAccess: [],
        memoryAccess: [],
        delegatesTo: [],
        sendsTo: [],
        other: [],
      };

      for (const edge of edges) {
        if (edge.f === agent.id && edge.t === agent.id) continue;

        if (edge.t === agent.id) {
          const source = byId.get(edge.f);
          if (!source || source.type === "control") continue;
          touchedIds.add(source.id);
          const link: CapabilityLink = { edge, node: source };
          switch (source.type) {
            case "input":
              group.receivesFrom.push(link);
              break;
            case "tool":
              group.usesTools.push(link);
              break;
            case "data":
              group.dataAccess.push(link);
              break;
            case "memory":
              group.memoryAccess.push(link);
              break;
            default:
              group.other.push(link);
          }
        }

        if (edge.f === agent.id) {
          const target = byId.get(edge.t);
          if (!target || target.type === "control") continue;
          touchedIds.add(target.id);
          const link: CapabilityLink = { edge, node: target };
          switch (target.type) {
            case "tool":
              group.usesTools.push(link);
              break;
            case "data":
              group.dataAccess.push(link);
              break;
            case "memory":
              group.memoryAccess.push(link);
              break;
            case "agent":
              group.delegatesTo.push(link);
              break;
            case "output":
              group.sendsTo.push(link);
              break;
            default:
              group.other.push(link);
          }
        }
      }

      return group;
    });

  const unassigned = nodes.filter((n) => n.type !== "agent" && n.type !== "control" && !touchedIds.has(n.id));

  return { agents, unassigned };
}
