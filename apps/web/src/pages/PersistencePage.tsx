import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api";
import { PersistenceChart } from "../components/Charts";
import { ErrorState, LoadingState, Panel, SectionHeading } from "../components/Common";
import type { PersistencePoint } from "../types";

export function PersistencePage() {
  const query = useQuery({ queryKey: ["persistence"], queryFn: () => apiGet<PersistencePoint[]>("/persistence") });
  if (query.isPending) return <LoadingState />;
  if (query.isError || !query.data) return <ErrorState message="Persistence data unavailable" />;
  return <div className="page-stack"><SectionHeading kicker="Persistence" title="How long objects remain in the tracked environment" description="Survival estimates distinguish confirmed decay from right-censored objects that are still present at the end of observation." /><Panel title="Kaplan–Meier persistence curves" subtitle="Launch cohort survival by normalized object class"><PersistenceChart data={query.data.data} /></Panel><div className="definition-grid"><article><span>Observed interval</span><strong>First valid epoch → confirmed decay</strong><p>Last observation alone is not treated as re-entry.</p></article><article><span>Right censoring</span><strong>Still tracked at study end</strong><p>Objects still present contribute partial duration without a false decay.</p></article><article><span>Comparison</span><strong>Category · regime · cohort</strong><p>Curves can be compared without confusing age with status.</p></article></div></div>;
}
