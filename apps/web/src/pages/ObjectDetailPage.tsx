import { useQuery } from "@tanstack/react-query";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { apiGet } from "../api";
import { ErrorState, LoadingState, Panel, SectionHeading } from "../components/Common";
import type { OrbitalObject } from "../types";

export function ObjectDetailPage() {
  const { noradId } = useParams();
  const [searchParams] = useSearchParams();
  const source = searchParams.get("source") === "current" ? "current" : "demo";
  const query = useQuery({ queryKey: ["object", noradId, source], queryFn: () => apiGet<OrbitalObject>(`/objects/${noradId}?source=${source}`) });
  if (query.isLoading) return <LoadingState />;
  if (query.error) return <ErrorState message="Object not found" />;
  const object = query.data!.data;
  return <div className="page-stack">
    <Link className="back-link" to={`/environment?mode=${source}`}>← Back to 3D environment</Link>
    <SectionHeading kicker={`NORAD ${object.norad_id} · ${source === "current" ? "Current catalog" : "Demo record"}`} title={object.name} description={`${object.international_designator} · ${object.country} · ${object.category.replaceAll("_", " ")}`} />
    <div className="object-detail-grid"><Panel title="Current analytical orbit" className="span-2"><div className="detail-metrics">{[["Mean altitude", `${object.altitude_km.toLocaleString()} km`], ["Perigee", `${object.perigee_km.toLocaleString()} km`], ["Apogee", `${object.apogee_km.toLocaleString()} km`], ["Inclination", `${object.inclination_deg}°`], ["Period", `${object.period_minutes} min`], ["Eccentricity", String(object.eccentricity)]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div></Panel><Panel title="Classification"><div className="classification-badge">{object.regime}</div><dl><dt>Normalized class</dt><dd>{object.category.replaceAll("_", " ")}</dd><dt>Launch date</dt><dd>{object.launch_date}</dd><dt>Record quality</dt><dd>{object.quality}</dd></dl></Panel></div>
  </div>;
}
