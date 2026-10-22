import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CalendarRange } from "lucide-react";
import { apiGet } from "../api";
import { PopulationChart } from "../components/Charts";
import { ErrorState, LoadingState, Panel, SectionHeading } from "../components/Common";
import type { TimelinePoint } from "../types";

export function EvolutionPage() {
  const query = useQuery({ queryKey: ["timeline", "full"], queryFn: () => apiGet<TimelinePoint[]>("/timeline") });
  if (query.isPending) return <LoadingState />; if (query.isError || !query.data) return <ErrorState message="Timeline unavailable" />;
  const latest = query.data.data.at(-1)!; const first = query.data.data[0];
  return <div className="page-stack"><SectionHeading kicker="Temporal analysis" title="How the environment got here" description="Distinct catalog objects across the space age, separated by what they became—not only what was launched." /><div className="insight-strip"><div><span>1957 baseline</span><strong>{first.total.toLocaleString()}</strong></div><ArrowRight /><div><span>2026 environment</span><strong>{latest.total.toLocaleString()}</strong></div><div className="insight-callout"><CalendarRange /><span>Annual history from 1957<br />Monthly detail from 2000</span></div></div><Panel title="Population by class" subtitle="1957–2026 · synthetic development release"><PopulationChart data={query.data.data} /></Panel></div>;
}
