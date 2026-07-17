import { describe, it, expect } from "vitest";
import { parse } from "yaml";
import { combineCrewaiYaml, buildCrewaiUpload } from "./crewai";

// Authentic CrewAI layout: each file's top level IS the mapping (bare).
const BARE_AGENTS = `support_agent:
  role: Support Agent
  tools:
    - name: gmail.send
`;
const BARE_TASKS = `triage_task:
  description: read and reply
  agent: support_agent
`;

describe("combineCrewaiYaml", () => {
  it("merges bare agents/tasks files into one agents:/tasks: document", () => {
    const doc = parse(combineCrewaiYaml(BARE_AGENTS, BARE_TASKS));
    expect(Object.keys(doc)).toEqual(["agents", "tasks"]);
    expect(doc.agents.support_agent.role).toBe("Support Agent");
    expect(doc.tasks.triage_task.agent).toBe("support_agent");
  });

  it("does not double-wrap files that already carry their section key", () => {
    const doc = parse(
      combineCrewaiYaml(`agents:\n${BARE_AGENTS.replace(/^/gm, "  ")}`, `tasks:\n${BARE_TASKS.replace(/^/gm, "  ")}`),
    );
    // agents.agents must NOT exist — the section was unwrapped, not nested again.
    expect(doc.agents.agents).toBeUndefined();
    expect(doc.agents.support_agent.role).toBe("Support Agent");
    expect(doc.tasks.triage_task.agent).toBe("support_agent");
  });

  it("emits an empty tasks mapping when the tasks file is absent/blank", () => {
    const doc = parse(combineCrewaiYaml(BARE_AGENTS, ""));
    expect(doc.tasks).toEqual({});
    expect(doc.agents.support_agent).toBeDefined();
  });

  it("regression: the merged document exposes a top-level agents mapping", () => {
    // The shipped bug uploaded only the agents file, which is a BARE mapping with
    // no `agents:` key -> the backend rejected it ("CrewAI 'agents' must be a
    // mapping"). The merge must restore that key.
    expect(parse(BARE_AGENTS).agents).toBeUndefined();
    expect(parse(combineCrewaiYaml(BARE_AGENTS, BARE_TASKS)).agents).toBeDefined();
  });
});

describe("buildCrewaiUpload", () => {
  it("combines the agents+tasks fields into a single parseable File", async () => {
    const file = await buildCrewaiUpload({
      agents: [new File([BARE_AGENTS], "agents.yaml")],
      tasks: [new File([BARE_TASKS], "tasks.yaml")],
    });
    expect(file).not.toBeNull();
    const doc = parse(await file!.text());
    expect(doc.agents.support_agent).toBeDefined();
    expect(doc.tasks.triage_task).toBeDefined();
  });

  it("merges with empty tasks when only the agents file is provided", async () => {
    const file = await buildCrewaiUpload({ agents: [new File([BARE_AGENTS], "agents.yaml")] });
    expect(file).not.toBeNull();
    const doc = parse(await file!.text());
    expect(doc.agents.support_agent).toBeDefined();
    expect(doc.tasks).toEqual({});
  });

  it("returns null when the required agents file is missing", async () => {
    expect(await buildCrewaiUpload({})).toBeNull();
    expect(await buildCrewaiUpload({ tasks: [new File([BARE_TASKS], "tasks.yaml")] })).toBeNull();
  });
});
