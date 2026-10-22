import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api";
import { CompositionChart } from "../components/Charts";
import { ErrorState, LoadingState, Panel, SectionHeading } from "../components/Common";
import type { DistributionBin } from "../types";

export function DistributionPage() {
  const altitude = useQuery({ queryKey: ["distribution", "altitude"], queryFn: () => apiGet<DistributionBin[]>("/distribution?dimension=altitude") });
  const regimes = useQuery({ queryKey: ["distribution", "regime"], queryFn: () => apiGet<DistributionBin[]>("/distribution?dimension=regime") });
  const composition = useQuery({ queryKey: ["distribution", "category"], queryFn: () => apiGet<DistributionBin[]>("/distribution?dimension=category") });
  if (altitude.isPending || regimes.isPending || composition.isPending) return <LoadingState />;
  if (altitude.isError || regimes.isError || composition.isError || !altitude.data || !regimes.data || !composition.data) return <ErrorState message="Distribution data unavailable" />;
  return <div className="page-stack"><SectionHeading kicker="Orbital distribution" title="Where the population accumulates" description="Compare altitude bands, analytical regimes and object composition without conflating count with physical density." /><div className="analysis-grid"><Panel title="Altitude bands" subtitle="Tracked object share" className="span-2"><div className="bar-list">{altitude.data.data.map((bin) => <div key={bin.label}><span>{bin.label}</span><div><i style={{ width: `${Math.max(2, bin.share * 100)}%` }} /></div><strong>{bin.count}</strong></div>)}</div></Panel><Panel title="Composition"><CompositionChart data={composition.data.data} /></Panel><Panel title="Analytical regimes" className="span-3"><div className="regime-cards">{regimes.data.data.map((item) => <article key={item.label}><span>{item.label.replace("_", "/")}</span><strong>{item.count}</strong><small>{(item.share * 100).toFixed(1)}% of sample</small></article>)}</div></Panel></div></div>;
}
