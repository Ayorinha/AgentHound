import { skinVars } from "@telefonica/mistica";
import { SEVERITY_STYLES, type Severity } from "@/lib/severity";
import { palette } from "@/lib/cyberSkin";
import type { NodeType } from "@/types/ThreatModel";

export function nodeFillColor(type: NodeType, risk?: "high" | "medium", status?: "present" | "absent"): string {
  switch (type) {
    case "input":
      return skinVars.colors.warningHigh;
    case "agent":
      // Not brandHigh: in dark mode that token is a 5%-opacity white overlay
      // (meant for subtle fills over content), so edges would show through the
      // node shape. `brand` is a fully opaque solid in both themes.
      return skinVars.colors.brand;
    case "tool":
      return skinVars.colors.successHigh;
    case "data":
      return risk === "high" ? skinVars.colors.errorHigh : skinVars.colors.warningHigh;
    case "output":
    case "memory":
      return skinVars.colors.promoHigh;
    case "control":
      // "High" variants (not the plain success/error tokens) so present/absent
      // labels stay legible against the node's background circle in both themes.
      return status === "present" ? skinVars.colors.successHigh : skinVars.colors.errorHigh;
    default:
      return skinVars.colors.brandHigh;
  }
}

// warningHigh (used by input nodes, and by data nodes with no/medium risk) is a
// light/mid-tone yellow in both themes, so white label text is unreadable on it.
// A fixed dark neutral, independent of the light/dark theme's own text tokens,
// keeps it legible either way.
export function nodeTextColor(type: NodeType, risk?: "high" | "medium"): string {
  const onWarningFill = type === "input" || (type === "data" && risk !== "high");
  return onWarningFill ? palette.grey900 : skinVars.colors.textPrimaryInverse;
}

export function severityAccentColor(severity: Severity, isDarkMode: boolean): string {
  const style = SEVERITY_STYLES[severity];
  return isDarkMode ? style.accentDark : style.accentLight;
}
