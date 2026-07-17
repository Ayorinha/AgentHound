/**
 * Cross-analysis aggregation for the Results dashboard.
 *
 * Everything here is derived from the stored-analyses list (`GET /analyses`),
 * whose per-item `summary` block already carries the finding counts and max
 * score — so the dashboard needs no per-analysis fetch (spec section 12.1).
 */

import { summarySeverity } from "@/lib/api/adapters";
import type { AnalysisListItem } from "@/lib/api/types";
import type { Severity } from "@/lib/severity";

/** One test in the "worst offenders" ranking. */
export interface RankedTest {
  id: string;
  name: string;
  framework: string;
  findings: number;
  critical: number;
  high: number;
  maxScore: number;
  severity: Severity;
}

/** One row of the by-framework distribution, sorted by finding volume. Carries
 * the full severity split so the dashboard can render a stacked severity bar. */
export interface FrameworkBreakdown {
  framework: string;
  tests: number;
  findings: number;
  critical: number;
  high: number;
  medium: number;
  /** Findings that are neither critical/high/medium (summary carries no explicit
   * low count, so it is the remainder). */
  low: number;
}

export interface ResultsAggregate {
  totalTests: number;
  totalFindings: number;
  totalCritical: number;
  totalHigh: number;
  /** Tests with at least one critical finding. */
  testsWithCritical: number;
  /** Percentage of tests carrying a critical, 0–100 (rounded). */
  criticalRate: number;
  /** Mean of each test's `max_score`, 1 decimal. */
  avgMaxScore: number;
  /** Top tests by risk (critical desc, then max score desc), links to results. */
  worstTests: RankedTest[];
  byFramework: FrameworkBreakdown[];
}

const WORST_LIMIT = 5;

/** Build the full dashboard aggregate from the raw analyses list. Empty-safe:
 * an empty list yields all-zero metrics and empty rankings. */
export function aggregateResults(items: AnalysisListItem[]): ResultsAggregate {
  const totalTests = items.length;
  let totalFindings = 0;
  let totalCritical = 0;
  let totalHigh = 0;
  let testsWithCritical = 0;
  let scoreSum = 0;

  const frameworkMap = new Map<string, FrameworkBreakdown>();

  for (const item of items) {
    const s = item.summary;
    totalFindings += s.findings;
    totalCritical += s.critical;
    totalHigh += s.high;
    scoreSum += s.max_score;
    if (s.critical > 0) testsWithCritical += 1;

    const fw = item.source_framework || "unknown";
    const entry =
      frameworkMap.get(fw) ??
      { framework: fw, tests: 0, findings: 0, critical: 0, high: 0, medium: 0, low: 0 };
    entry.tests += 1;
    entry.findings += s.findings;
    entry.critical += s.critical;
    entry.high += s.high;
    entry.medium += s.medium;
    // The summary has no explicit low count; it is whatever is left over.
    entry.low += Math.max(0, s.findings - s.critical - s.high - s.medium);
    frameworkMap.set(fw, entry);
  }

  const worstTests: RankedTest[] = items
    .map((item) => ({
      id: item.analysis_id,
      name: item.name,
      framework: item.source_framework,
      findings: item.summary.findings,
      critical: item.summary.critical,
      high: item.summary.high,
      maxScore: item.summary.max_score,
      severity: summarySeverity(item.summary),
    }))
    .sort((a, b) => b.critical - a.critical || b.maxScore - a.maxScore || b.findings - a.findings)
    .slice(0, WORST_LIMIT);

  const byFramework = Array.from(frameworkMap.values()).sort(
    (a, b) => b.findings - a.findings || b.critical - a.critical,
  );

  return {
    totalTests,
    totalFindings,
    totalCritical,
    totalHigh,
    testsWithCritical,
    criticalRate: totalTests === 0 ? 0 : Math.round((100 * testsWithCritical) / totalTests),
    avgMaxScore: totalTests === 0 ? 0 : Number((scoreSum / totalTests).toFixed(1)),
    worstTests,
    byFramework,
  };
}
