import AnalysisResultScreen from "@/screens/AnalysisResultScreen";

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ from?: string }>;
}) {
  const { id } = await params;
  const { from } = await searchParams;
  // Where the "back" link returns to, based on the entry point. Defaults to the
  // overview; the results dashboard passes ?from=results when it links here.
  const backTo = from === "results" ? "results" : "overview";
  return <AnalysisResultScreen analysisId={id} backTo={backTo} />;
}
