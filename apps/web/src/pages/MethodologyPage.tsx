import { ExternalLink } from "lucide-react";
import { Panel, SectionHeading } from "../components/Common";

const definitions = [
  { term: "Population", answer: "One record per physical object", detail: "A physical catalog record is counted once per snapshot using its distinct NORAD catalog identifier. Historical element sets are observations, not additional objects." },
  { term: "Concentration", answer: "Catalog density, not collision risk", detail: "Altitude–inclination bins measure catalog concentration. Approximate shell-volume density is separate and is never presented as collision probability." },
  { term: "Persistence", answer: "First observation to confirmed decay", detail: "Duration begins at the first valid observation and ends at confirmed decay. Still-tracked records are right-censored." },
  { term: "Scope boundary", answer: "Public catalogs only", detail: "Public catalogs omit classified and untracked populations. Model estimates remain separate from individually tracked objects." },
];

const canonicalSources = [
  { name: "Space-Track", role: "Historical GP and SATCAT", group: "Orbital elements", url: "https://www.space-track.org" },
  { name: "CelesTrak", role: "Current validation and status", group: "Orbital elements", url: "https://celestrak.org" },
  { name: "GCAT", role: "Object lifecycle metadata", group: "Lifecycle & events", url: "https://planet4589.org/space/gcat" },
  { name: "NASA ODPO", role: "Fragmentation history", group: "Lifecycle & events", url: "https://orbitaldebris.jsc.nasa.gov" },
  { name: "ESA DISCOS", role: "Launch and fragmentation provenance", group: "Lifecycle & events", url: "https://discosweb.esoc.esa.int" },
  { name: "UCS Satellite Database", role: "Operator, purpose and users for active payloads", group: "Operator context", url: "https://www.ucsusa.org/resources/satellite-database" },
];

export function MethodologyPage() {
  return <div className="page-stack"><SectionHeading kicker="Methodology" title="Reproducible by design" description="Every chart is tied to explicit definitions, versioned transformations, source attribution and known limits." /><div className="definition-grid methodology-grid">{definitions.map((item) => <article key={item.term}><span>{item.term}</span><strong>{item.answer}</strong><p>{item.detail}</p></article>)}</div><Panel title="Canonical sources" subtitle="Every object category rendered in the 3D environment traces back to one of these six records"><div className="source-list">{canonicalSources.map((source) => <a key={source.name} href={source.url} target="_blank" rel="noreferrer"><div><span className="source-group">{source.group}</span><strong>{source.name}</strong><span>{source.role}</span></div><ExternalLink size={16} /></a>)}</div></Panel></div>;
}
