import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { apiGet } from "../api";
import { ErrorState, LoadingState, Panel, SectionHeading } from "../components/Common";
import type { OrbitalEvent } from "../types";

export function EventDetailPage() {
  const { eventId } = useParams();
  const query = useQuery({ queryKey: ["event", eventId], queryFn: () => apiGet<OrbitalEvent>(`/events/${eventId}`) });
  if (query.isLoading) return <LoadingState />; if (query.error) return <ErrorState message="Event not found" />;
  const event = query.data!.data;
  return <div className="page-stack"><Link className="back-link" to="/events">← All events</Link><SectionHeading kicker={`${event.date} · ${event.event_type}`} title={event.name} description={event.description} /><div className="detail-metrics event-detail">{[["Assessed cause", event.assessed_cause], ["Catalogued fragments", event.fragments_catalogued.toLocaleString()], ["Reference survivors", event.fragments_remaining.toLocaleString()], ["Event altitude", `${event.altitude_km} km`], ["Inclination", `${event.inclination_deg}°`]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div><Panel title="Before and after"><div className="before-after"><div><span>365 days before</span><strong>Baseline environment</strong><i /></div><div className="event-pulse"><span>Event</span></div><div><span>365 days after</span><strong>Persistent cohort introduced</strong><i className="after" /></div></div></Panel></div>;
}
