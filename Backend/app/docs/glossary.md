# Glossary

Plain-language definitions of the technical terms used in this backend.

- **IR (Internal Representation).** The single normalized data structure every
  input is converted into (nodes + capability edges), regardless of the source
  framework. Everything downstream (graph, rules, findings) reads the IR, so the
  rest of the system does not care whether the input was CrewAI, Dify or generic.

- **Capability edge.** A directed connection between two nodes labelled with a
  neutral verb (`read`, `send`, `fetchWeb`, ...). The verb says *what* happens;
  whether it is risky is decided from the target node's properties, not the verb.

- **Node type.** One of `agent, input, tool, data_asset, output, memory, control`.
  Each carries risk-relevant properties (e.g. an input's `trust_level`, an
  output's `boundary` and `approval_gate_present`).

- **Safe default.** When an input omits a property, the normalizer fills in the
  most cautious value (e.g. an input is `untrusted`, an output is `external`), so
  the analysis never under-reports because of a missing field.

- **DFS (Depth-First Search).** A way of walking a graph: follow one branch as
  far as it goes, then back up and try the next. It is the classic method for
  enumerating paths between two nodes. We do not hand-write it — NetworkX's
  `all_simple_paths` does the traversal for us — but `max_depth` exists to bound
  exactly this kind of search so it cannot explode on large graphs.

- **NetworkX / MultiDiGraph.** NetworkX is a Python graph library. A
  *MultiDiGraph* is a directed graph that allows more than one edge between the
  same two nodes — needed here because one agent may have several capabilities
  over the same target.

- **Pydantic (v2).** A Python data-validation library. You declare the expected
  shape of data as typed classes; Pydantic validates and parses incoming data
  against that shape and rejects anything malformed. FastAPI uses it to validate
  requests/responses and to auto-generate the `/docs` API reference.

- **FastAPI / uvicorn.** FastAPI is the web framework that defines the HTTP
  endpoints; uvicorn is the ASGI server process that actually runs the app.

- **Finding.** A single detected risk, produced by a rule. It carries the rule
  id, a severity, a numeric score, the node path, evidence, and recommended
  controls.

- **Rule (FH-xxx).** A declarative risk pattern (e.g. FH-001 = full exfiltration
  path). Rules match against the graph and emit findings.

- **Attack path / capability path.** An ordered chain of nodes and capabilities
  that, taken together, represents a way risk propagates — e.g. untrusted input →
  agent → sensitive read → external send.

- **Finding class (attack vs hygiene).** Every finding is labelled `attack` or
  `hygiene`. An *attack* finding is an exploitable capability path; a *hygiene*
  finding is a compliance or good-practice gap that fires on default
  configurations (e.g. an unclassified data asset, a full-auto agent without an
  audit trail). The label is derived from `HYGIENE_RULE_IDS` and lets the UI show
  the two as separate channels so hygiene volume does not bury the attack paths.

- **Control.** A mitigation (e.g. `humanInTheLoop`). In Phase 1 controls appear
  only as recommendations on findings; applying/simulating them is Phase 2.
