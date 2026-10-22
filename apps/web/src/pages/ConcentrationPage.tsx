import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api";
import { ConcentrationHeatmap } from "../components/Charts";
import { ErrorState, LoadingState, Panel, SectionHeading } from "../components/Common";
import type { ConcentrationCell } from "../types";

export function ConcentrationPage() {
  const query = useQuery({ queryKey: ["concentration"], queryFn: () => apiGet<ConcentrationCell[]>("/concentration") });
  if (query.isPending) return <LoadingState />; if (query.isError || !query.data) return <ErrorState message="Concentration data unavailable" />;
  const hottest = [...query.data.data].sort((a, b) => b.count - a.count).slice(0, 5);
  return <div className="page-stack"><SectionHeading kicker="Concentration analytics" title="The orbital shell has neighborhoods" description="The heatmap counts tracked objects by altitude and inclination. Shell-normalized density is reported separately." /><div className="analysis-grid"><Panel title="Altitude × inclination" subtitle="LEO catalog concentration" className="span-2"><ConcentrationHeatmap data={query.data.data} /></Panel><Panel title="Highest concentration cells" subtitle="Ranked by tracked-object count"><div className="rank-list">{hottest.map((cell, index) => <div key={`${cell.altitude_start_km}-${cell.inclination_start_deg}`}><b>{String(index + 1).padStart(2, "0")}</b><span>{cell.altitude_start_km}–{cell.altitude_end_km} km<br /><small>{cell.inclination_start_deg}–{cell.inclination_end_deg}° inclination</small></span><strong>{cell.count}</strong></div>)}</div></Panel></div></div>;
}
