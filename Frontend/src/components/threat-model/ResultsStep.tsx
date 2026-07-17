"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useTranslations } from "next-intl";
import {
  Align,
  Box,
  Boxed,
  BoxedAccordion,
  BoxedAccordionItem,
  ButtonPrimary,
  ButtonSecondary,
  Callout,
  Circle,
  DataCard,
  Divider,
  Grid,
  IconArrowLineRightRegular,
  IconCheckFilled,
  IconDownloadRegular,
  IconRobotRegular,
  IconShieldCheckedOkRegular,
  IconTargetRegular,
  Inline,
  Spinner,
  Stack,
  Tabs,
  Tag,
  Text1,
  Text2,
  Text4,
  Text6,
  Timeline,
  TimelineItem,
  skinVars,
  useTheme,
} from "@telefonica/mistica";
import type { IconProps } from "@telefonica/mistica";
import SeverityBadge from "@/components/threat-model/SeverityBadge";
import InlineError from "@/components/ui/InlineError";
import { severityAccentColor } from "@/lib/threatModelColors";
import { SEVERITY_STYLES } from "@/lib/severity";
import type { AnalysisResult, ChokepointRec } from "@/lib/api/adapters";
import {
  downloadFindingsJson,
  downloadGraphJson,
  downloadMarkdownReport,
  downloadYaml,
} from "@/lib/threatModelExport";
import type { Finding } from "@/types/ThreatModel";
import type { ReactElement } from "react";

// The graph is a large, decorative SVG only needed once a user reaches this step of the
// wizard — keep it out of the initial results-step bundle.
const CapabilityGraph = dynamic(() => import("@/components/threat-model/CapabilityGraph"), {
  ssr: false,
  loading: () => (
    <Boxed>
      <Box paddingY={64}>
        <Align x="center">
          <Spinner size={24} color={skinVars.colors.brand} />
        </Align>
      </Box>
    </Boxed>
  ),
});

interface MetricRowProps {
  label: string;
  value: string | number;
  color?: string;
}

function MetricRow({ label, value, color }: MetricRowProps) {
  return (
    <Inline space="between" alignItems="baseline">
      <Text1 regular color={skinVars.colors.textSecondary}>{label}</Text1>
      <Text1 medium color={color}>{value}</Text1>
    </Inline>
  );
}

interface BeforeAfterCardProps {
  label: string;
  Icon: (props: IconProps) => ReactElement;
  color: string;
  rows: { label: string; value: string | number; color?: string }[];
}

function BeforeAfterCard({ label, Icon, color, rows }: BeforeAfterCardProps) {
  return (
    <Boxed>
      <Box paddingX={20} paddingY={20}>
        <Stack space={16}>
          <Inline space={12} alignItems="center">
            <Circle size={32} backgroundColor={skinVars.colors.neutralLow}>
              <Icon size={18} color={color} />
            </Circle>
            <Text2 medium color={color}>{label}</Text2>
          </Inline>
          <Divider />
          <Stack space={8}>
            {rows.map((row) => (
              <MetricRow key={row.label} label={row.label} value={row.value} color={row.color} />
            ))}
          </Stack>
        </Stack>
      </Box>
    </Boxed>
  );
}

interface FindingCardProps {
  finding: Finding;
  isDarkMode: boolean;
  tSeverity: (key: string) => string;
  scoreLabel: string;
}

function FindingCard({ finding, isDarkMode, tSeverity, scoreLabel }: FindingCardProps) {
  const accent = severityAccentColor(finding.severity, isDarkMode);
  const hasRefs = Boolean(
    finding.owaspAgentic?.length || finding.owaspLlm?.length || finding.mitre?.length,
  );
  return (
    <Boxed>
      <Box paddingX={20} paddingY={16}>
        <Stack space={12}>
          <Inline space="between" alignItems="center">
            <Inline space={8} alignItems="center" wrap verticalSpace={4}>
              <SeverityBadge severity={finding.severity} small>{tSeverity(finding.severity)}</SeverityBadge>
              <Text1 medium color={skinVars.colors.textSecondary}>{finding.ruleId}</Text1>
              <Tag type="inactive" small>{finding.category}</Tag>
            </Inline>
            <Text2 medium color={accent}>{scoreLabel}: {finding.score}</Text2>
          </Inline>
          <Stack space={4}>
            <Text2 medium>{finding.title}</Text2>
            {finding.desc && <Text1 regular color={skinVars.colors.textSecondary}>{finding.desc}</Text1>}
            {finding.evidence && Object.keys(finding.evidence).length > 0 && (
              <Text1 regular color={skinVars.colors.textSecondary}>
                {Object.entries(finding.evidence)
                  .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join("/") : value}`)
                  .join(" · ")}
              </Text1>
            )}
          </Stack>
          {hasRefs && (
            <Inline space={4} wrap verticalSpace={4}>
              {finding.owaspAgentic?.map((tag) => <Tag key={tag} small type="inactive">{`Agentic ${tag}`}</Tag>)}
              {finding.owaspLlm?.map((tag) => <Tag key={tag} small type="inactive">{tag}</Tag>)}
              {finding.mitre?.map((tag) => <Tag key={tag} small type="inactive">{tag}</Tag>)}
            </Inline>
          )}
        </Stack>
      </Box>
    </Boxed>
  );
}

function ChokepointCallout({ rec }: { rec: ChokepointRec }) {
  const t = useTranslations("results");
  return (
    <Callout
      title={t("chokepointTitle")}
      description={t("chokepointDesc", {
        control: rec.controlName,
        node: rec.targetNodeLabel,
        reduction: rec.estimatedReduction,
        pct: rec.riskReductionPct,
        cost: rec.costEstimate,
      })}
      asset={<IconArrowLineRightRegular color={skinVars.colors.brand} />}
    />
  );
}

interface ResultsStepProps {
  result: AnalysisResult | null;
  hideTitle?: boolean;
}

function ResultsStep({ result, hideTitle = false }: ResultsStepProps) {
  const t = useTranslations("results");
  const tSeverity = useTranslations("overview.severity");
  const tCommon = useTranslations("common");
  const { isDarkMode } = useTheme();
  const [tab, setTab] = useState(0);
  const solved = tab === 1;
  const view = solved ? "solution" : "findings";

  if (!result) {
    return <InlineError message={tCommon("error.description")} />;
  }

  const { counts, findings } = result;
  const sol = result.solution;
  const findingGroups = (["attack", "hygiene"] as const)
    .map((cls) => ({ cls, items: findings.filter((f: Finding) => f.findingClass === cls) }))
    .filter(({ items }) => items.length > 0);
  // The Proposed Solution tab needs the live simulation; if it failed to load
  // (Phase 2 unavailable), surface a notice rather than a misleading green graph.
  const solutionUnavailable = solved && !sol;

  return (
    <Stack space={32}>
      <Stack space={4}>
        {!hideTitle && result.name && (
          <Text1 regular color={skinVars.colors.textSecondary}>{t("title")}</Text1>
        )}
        {!hideTitle && <Text4 medium as="h1">{result.name || t("title")}</Text4>}
        <Text2 regular color={skinVars.colors.textSecondary}>
          {t("subtitleTemplate", {
            agents: counts.agents,
            tools: counts.tools,
            data: counts.dataAssets,
            findings: counts.findings,
            critical: counts.critical,
          })}
        </Text2>
      </Stack>

      <Tabs
        selectedIndex={tab}
        onChange={setTab}
        tabs={[
          { text: `${t("tabFindings")} (${counts.findings})` },
          { text: t("tabProposedSolution") },
        ]}
      />

      {solutionUnavailable ? (
        <InlineError message={tCommon("error.description")} />
      ) : (
        <Stack space={32}>
          <Stack space={16}>
            <Stack space={4}>
              <Text4 medium as="h2">{solved ? t("graphTitleSolution") : t("graphTitleFindings")}</Text4>
              <Text2 regular color={skinVars.colors.textSecondary}>{solved ? t("graphDescSolution") : t("graphDescFindings")}</Text2>
            </Stack>
            <CapabilityGraph
              solved={solved}
              nodes={solved && sol ? sol.nodes : result.nodes}
              edges={solved && sol ? sol.edges : result.edges}
              findings={findings}
              name={result.name}
              attacks={solved && sol ? sol.attacks : result.attacks}
              appliedControlCount={solved && sol ? sol.appliedControlCount : undefined}
              nodeControlInfo={solved && sol ? sol.nodeControlInfo : undefined}
              edgeControlInfo={solved && sol ? sol.edgeControlInfo : undefined}
            />
          </Stack>

          <Stack space={16}>
            <Text4 medium as="h2">{solved ? t("metricsTitleSolution") : t("metricsTitleFindings")}</Text4>
            {!solved ? (
              <Grid columns={{ minSize: 150 }} gap={16}>
                <DataCard
                  width="100%"
                  asset={
                    <Circle size={32} backgroundColor={skinVars.colors.neutralLow}>
                      <SEVERITY_STYLES.critical.Icon size={18} color={severityAccentColor("critical", isDarkMode)} />
                    </Circle>
                  }
                  title={t("kpis.critical")}
                  slot={<Text6 color={severityAccentColor("critical", isDarkMode)}>{counts.critical}</Text6>}
                />
                <DataCard
                  width="100%"
                  asset={
                    <Circle size={32} backgroundColor={skinVars.colors.neutralLow}>
                      <SEVERITY_STYLES.high.Icon size={18} color={severityAccentColor("high", isDarkMode)} />
                    </Circle>
                  }
                  title={t("kpis.high")}
                  slot={<Text6 color={severityAccentColor("high", isDarkMode)}>{counts.high}</Text6>}
                />
                <DataCard
                  width="100%"
                  asset={
                    <Circle size={32} backgroundColor={skinVars.colors.neutralLow}>
                      <SEVERITY_STYLES.medium.Icon size={18} color={severityAccentColor("medium", isDarkMode)} />
                    </Circle>
                  }
                  title={t("kpis.medium")}
                  slot={<Text6 color={severityAccentColor("medium", isDarkMode)}>{counts.medium}</Text6>}
                />
                <DataCard
                  width="100%"
                  asset={
                    <Circle size={32} backgroundColor={skinVars.colors.neutralLow}>
                      <SEVERITY_STYLES.low.Icon size={18} color={severityAccentColor("low", isDarkMode)} />
                    </Circle>
                  }
                  title={t("kpis.low")}
                  slot={<Text6 color={severityAccentColor("low", isDarkMode)}>{counts.low}</Text6>}
                />
                <DataCard
                  width="100%"
                  asset={
                    <Circle size={32} backgroundColor={skinVars.colors.neutralLow}>
                      <IconTargetRegular size={18} color={severityAccentColor("critical", isDarkMode)} />
                    </Circle>
                  }
                  title={t("kpis.maxScore")}
                  slot={<Text6 color={severityAccentColor("critical", isDarkMode)}>{counts.maxScore}</Text6>}
                />
                <DataCard
                  width="100%"
                  asset={
                    <Circle size={32} backgroundColor={skinVars.colors.neutralLow}>
                      <IconRobotRegular size={18} color={skinVars.colors.neutralHigh} />
                    </Circle>
                  }
                  title={t("kpis.agents")}
                  slot={<Text6 color={skinVars.colors.neutralHigh}>{counts.agents}</Text6>}
                />
              </Grid>
            ) : (
              sol && (
                <Inline space={16} alignItems="center" expand={[0, 2]}>
                  <BeforeAfterCard
                    label={t("before")}
                    Icon={SEVERITY_STYLES.critical.Icon}
                    color={severityAccentColor("critical", isDarkMode)}
                    rows={[
                      { label: t("beforeAfter.findingCount"), value: sol.beforeAfter.before.findingCount, color: severityAccentColor("critical", isDarkMode) },
                      { label: t("beforeAfter.criticalCount"), value: sol.beforeAfter.before.criticalCount, color: severityAccentColor("critical", isDarkMode) },
                      { label: t("beforeAfter.maxScore"), value: sol.beforeAfter.before.maxScore, color: severityAccentColor("critical", isDarkMode) },
                      { label: t("beforeAfter.riskScoreTotal"), value: sol.beforeAfter.before.riskScoreTotal },
                    ]}
                  />
                  <IconArrowLineRightRegular color={skinVars.colors.brand} />
                  <BeforeAfterCard
                    label={t("after")}
                    Icon={IconShieldCheckedOkRegular}
                    color={severityAccentColor("none", isDarkMode)}
                    rows={[
                      { label: t("beforeAfter.findingCount"), value: sol.beforeAfter.after.findingCount, color: severityAccentColor("none", isDarkMode) },
                      { label: t("beforeAfter.criticalCount"), value: sol.beforeAfter.after.criticalCount, color: severityAccentColor("none", isDarkMode) },
                      { label: t("beforeAfter.maxScore"), value: sol.beforeAfter.after.maxScore, color: severityAccentColor("none", isDarkMode) },
                      { label: t("beforeAfter.riskReduction"), value: sol.beforeAfter.after.riskReduction, color: severityAccentColor("none", isDarkMode) },
                    ]}
                  />
                </Inline>
              )
            )}
          </Stack>

          {!solved && result.solution?.chokepointRec && (
            <ChokepointCallout rec={result.solution.chokepointRec} />
          )}

          {!solved ? (
            findingGroups.length > 0 && (
              <BoxedAccordion>
                {findingGroups.map(({ cls, items }) => (
                  <BoxedAccordionItem
                    key={cls}
                    title={cls === "attack" ? t("attackFindingsTitle") : t("hygieneTitle")}
                    right={<Tag type="inactive" small>{`${items.length}`}</Tag>}
                    content={
                      <Stack space={12}>
                        {items.map((f: Finding) => (
                          <FindingCard
                            key={f.id}
                            finding={f}
                            isDarkMode={isDarkMode}
                            tSeverity={tSeverity}
                            scoreLabel={t("tableHeaders.score")}
                          />
                        ))}
                      </Stack>
                    }
                  />
                ))}
              </BoxedAccordion>
            )
          ) : (
            sol && (
              <BoxedAccordion>
                {[
                  sol.remediation.length > 0 ? (
                    <BoxedAccordionItem
                      key="controls"
                      title={t("controlsTitle")}
                      right={<Tag type="active" small>{`${sol.remediation.length}`}</Tag>}
                      content={
                        <Timeline>
                          {sol.remediation.map((step) => (
                            <TimelineItem
                              key={step.title}
                              state={step.done ? "completed" : "active"}
                              asset={step.done ? { kind: "circled-icon", Icon: IconCheckFilled } : undefined}
                            >
                              <Stack space={2}>
                                <Text2 medium>{step.title}</Text2>
                                <Text1 regular color={skinVars.colors.textSecondary}>{step.desc}</Text1>
                              </Stack>
                            </TimelineItem>
                          ))}
                        </Timeline>
                      }
                    />
                  ) : null,
                  <BoxedAccordionItem
                    key="resolved"
                    title={t("resolved")}
                    right={<Tag type="success" small>{`${findings.length}`}</Tag>}
                    content={
                      <Stack space={8}>
                        {findings.map((f) => (
                          <Boxed key={f.id}>
                            <Box padding={16}>
                              <Stack space={8}>
                                <Inline space={8} alignItems="center">
                                  <IconCheckFilled color={skinVars.colors.success} />
                                  <Text2 medium>{f.ruleId} — {f.title}</Text2>
                                  <Tag type="success">{t("resolved")}</Tag>
                                </Inline>
                                <Inline space={4} wrap verticalSpace={4}>
                                  {f.controls?.map((c) => <Tag key={c} type="success" small>{c}</Tag>)}
                                </Inline>
                              </Stack>
                            </Box>
                          </Boxed>
                        ))}
                      </Stack>
                    }
                  />,
                ].filter(Boolean)}
              </BoxedAccordion>
            )
          )}

          <Boxed>
            <Box paddingX={20} paddingY={20}>
              <Stack space={16}>
                <Inline space={12} alignItems="center">
                  <Circle size={32} backgroundColor={skinVars.colors.neutralLow}>
                    <IconDownloadRegular size={18} color={skinVars.colors.brand} />
                  </Circle>
                  <Stack space={2}>
                    <Text2 medium>{solved ? t("exportTitleSolution") : t("exportTitleFindings")}</Text2>
                    <Text1 regular color={skinVars.colors.textSecondary}>
                      {solved ? t("exportDescSolution") : t("exportDescFindings")}
                    </Text1>
                  </Stack>
                </Inline>
                <Inline space={12} wrap verticalSpace={12}>
                  <ButtonPrimary
                    small
                    onPress={() => downloadMarkdownReport(result, view)}
                    StartIcon={IconDownloadRegular}
                  >
                    {t("exportReportMd")}
                  </ButtonPrimary>
                  <ButtonSecondary
                    small
                    onPress={() =>
                      downloadGraphJson(
                        result,
                        view,
                        solved && sol ? sol.nodes : result.nodes,
                        solved && sol ? sol.edges : result.edges,
                        solved && sol ? sol.attacks : result.attacks,
                      )
                    }
                    StartIcon={IconDownloadRegular}
                  >
                    {t("exportGraphJson")}
                  </ButtonSecondary>
                  <ButtonSecondary
                    small
                    onPress={() => downloadFindingsJson(result)}
                    StartIcon={IconDownloadRegular}
                  >
                    {t("exportFindingsJson")}
                  </ButtonSecondary>
                  <ButtonSecondary
                    small
                    onPress={() => downloadYaml(view, result)}
                    StartIcon={IconDownloadRegular}
                  >
                    {t("exportButton")}
                  </ButtonSecondary>
                </Inline>
              </Stack>
            </Box>
          </Boxed>
        </Stack>
      )}
    </Stack>
  );
}

export default ResultsStep;
