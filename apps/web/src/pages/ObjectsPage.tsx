import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiGet } from "../api";
import { ErrorState, LoadingState, Panel, SectionHeading } from "../components/Common";
import type { OrbitalObject } from "../types";

export function ObjectsPage() {
  const query = useQuery({ queryKey: ["objects"], queryFn: () => apiGet<OrbitalObject[]>("/objects/search?limit=50") });
  if (query.isPending) return <LoadingState />;
  if (query.isError || !query.data) return <ErrorState message="Object index unavailable" />;
  return <div className="page-stack"><SectionHeading kicker="Object index" title="Inspect the records behind the environment" description="Object drill-down supports the collective analysis; it is not the product's primary frame." /><Panel><div className="object-table" role="table"><div className="table-row table-head" role="row"><span>NORAD</span><span>Name</span><span>Class</span><span>Regime</span><span>Altitude</span><span>Quality</span></div>{query.data.data.map((item) => <Link className="table-row" role="row" key={item.norad_id} to={`/objects/${item.norad_id}`}><span>{item.norad_id}</span><strong>{item.name}</strong><span>{item.category.replaceAll("_", " ")}</span><span>{item.regime}</span><span>{item.altitude_km.toLocaleString()} km</span><span className={`quality-${item.quality}`}>{item.quality}</span></Link>)}</div></Panel></div>;
}
