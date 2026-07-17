import { parse, stringify } from "yaml";

/**
 * CrewAI describes a crew across two files — `agents.yaml` and `tasks.yaml`.
 * The backend adapter, however, ingests a SINGLE YAML document with top-level
 * `agents:` and `tasks:` mappings (that is what `detect_framework` keys on).
 * The wizard therefore has to merge the two uploaded files into that shape
 * before calling `POST /analyses`; sending only one file (the historical bug)
 * either errors on the missing `agents:` key or silently drops the tasks.
 */

/**
 * Return the section mapping from one uploaded CrewAI file.
 *
 * Authentic CrewAI `agents.yaml` / `tasks.yaml` put the mapping at the top
 * level (the agent/task names ARE the top-level keys). Some exports instead
 * nest it under the section key (`agents:` / `tasks:`). Accept both so a user
 * cannot get a wrong result from a defensible file layout.
 */
function sectionMapping(text: string, key: "agents" | "tasks"): unknown {
  const doc = parse(text) ?? {};
  if (doc && typeof doc === "object" && !Array.isArray(doc) && key in (doc as Record<string, unknown>)) {
    return (doc as Record<string, unknown>)[key];
  }
  return doc;
}

/**
 * Merge CrewAI's separate agents/tasks file contents into the single
 * `agents:`/`tasks:` YAML document the backend adapter requires.
 *
 * `tasksText` may be empty (the backend tolerates an empty `tasks` mapping);
 * `agentsText` is required by the caller before this runs.
 */
export function combineCrewaiYaml(agentsText: string, tasksText: string): string {
  const merged: Record<string, unknown> = {
    agents: sectionMapping(agentsText, "agents"),
    tasks: tasksText.trim() ? sectionMapping(tasksText, "tasks") : {},
  };
  return stringify(merged);
}

/**
 * Build the single File the backend expects from the wizard's field-keyed
 * CrewAI uploads. Returns null when the required agents file is missing so the
 * caller can surface a validation error instead of uploading a broken document.
 */
export async function buildCrewaiUpload(
  filesByField: Record<string, File[]>,
): Promise<File | null> {
  const agentsFile = filesByField.agents?.[0];
  const tasksFile = filesByField.tasks?.[0];
  if (!agentsFile) return null;
  const agentsText = await agentsFile.text();
  const tasksText = tasksFile ? await tasksFile.text() : "";
  const combined = combineCrewaiYaml(agentsText, tasksText);
  return new File([combined], "crewai-combined.yaml", { type: "application/x-yaml" });
}
