import { useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { apiGet } from "../api";
import { ErrorState, LoadingState, SectionHeading } from "../components/Common";
import type { OrbitalEvent } from "../types";

export function EventsPage() {
  const query = useQuery({ queryKey: ["events"], queryFn: () => apiGet<OrbitalEvent[]>("/events") });
  if (query.isPending) return <LoadingState />;
  if (query.isError || !query.data) return <ErrorState message="Event data unavailable" />;
  return <div className="page-stack"><SectionHeading kicker="Event analysis" title="Orbit does not reset" description="Fragmentation is a moment; its population effect can persist for decades." /><div className="event-list">{query.data.data.map((event) => <article className="event-card" key={event.id}><div className="event-year"><span>{event.date.slice(0, 4)}</span><i /></div><div><div className="event-tags"><span>{event.event_type}</span>{event.deep_replay && <span>Deep replay</span>}</div><h3>{event.name}</h3><p>{event.description}</p><div className="event-stats"><span><b>{event.fragments_catalogued.toLocaleString()}</b> catalogued fragments</span><span><b>{event.fragments_remaining.toLocaleString()}</b> remaining in reference record</span><span><b>{event.altitude_km} km</b> event altitude</span></div></div><Link className="icon-button" to={`/events/${event.id}`} aria-label={`Open ${event.name}`}><ArrowRight /></Link></article>)}</div></div>;
}
