import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Download, Globe2 } from "lucide-react";
import { Link } from "react-router-dom";
import { apiGet, exportUrl } from "../api";
import { CompositionChart, PopulationChart } from "../components/Charts";
import { ErrorState, FreshnessBanner, LoadingState, MetricCard, Panel, SectionHeading } from "../components/Common";
import type { DistributionBin, Overview, TimelinePoint } from "../types";

export function OverviewPage() {
  const overview = useQuery({ queryKey: ["overview"], queryFn: () => apiGet<Overview>("/overview") });
  const timeline = useQuery({ queryKey: ["timeline", 2000], queryFn: () => apiGet<TimelinePoint[]>("/timeline?start=2000") });
  const composition = useQuery({ queryKey: ["distribution", "category"], queryFn: () => apiGet<DistributionBin[]>("/distribution?dimension=category") });
  if (overview.isLoading || timeline.isLoading || composition.isLoading) return <LoadingState />;
  if (overview.error || timeline.error || composition.error) return <ErrorState message="The analytics API did not return a complete overview." />;
  const data = overview.data!.data;
  return <div className="page-stack">
    <FreshnessBanner meta={overview.data!.meta} />
    <SectionHeading kicker="System view" title="The orbital shell, read as one environment" description="Tracked populations, structural change and persistent event effects—without reducing the story to a list of satellites." action={<a className="button button-secondary" href={exportUrl("/exports/timeline.csv")}><Download size={16} />Export timeline</a>} />
    <div className="metric-grid"><MetricCard label="Tracked environment" value={data.total_objects.toLocaleString()} detail="catalogued objects" change={data.change_yoy_percent} /><MetricCard label="Active payloads" value={data.active_payloads.toLocaleString()} detail="reported operational" tone="blue" /><MetricCard label="Debris" value={data.debris.toLocaleString()} detail="catalogued fragments" tone="red" /><MetricCard label="Modeled >1 cm" value={`${(data.modeled_over_1cm / 1_000_000).toFixed(1)}M`} detail="statistical estimate" tone="amber" /></div>
    <div className="hero-grid"><Panel title="Population evolution" subtitle="Distinct tracked objects · 2000–2026" className="span-2"><PopulationChart data={timeline.data!.data} compact /></Panel><Panel title="Environment composition" subtitle="Current normalized classes"><CompositionChart data={composition.data!.data} /></Panel></div>
    <section className="explore-cta"><div className="explore-icon"><Globe2 /></div><div><span className="eyebrow">INTERACTIVE ENVIRONMENT</span><h2>See the structure behind the totals</h2><p>Move from current orbital points to historical snapshots and event-driven changes.</p></div><Link to="/environment" className="button button-primary">Open 3D environment <ArrowRight size={17} /></Link></section>
  </div>;
}

