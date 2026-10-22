import { AlertTriangle, ArrowDownRight, ArrowUpRight, Database, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";
import type { Meta } from "../types";

export function LoadingState({ label = "Loading environment data" }: { label?: string }) {
  return <div className="state-panel"><LoaderCircle className="spin" /><strong>{label}</strong></div>;
}

export function ErrorState({ message }: { message: string }) {
  return <div className="state-panel error"><AlertTriangle /><strong>Unable to load this view</strong><span>{message}</span></div>;
}

export function FreshnessBanner({ meta }: { meta?: Meta }) {
  if (!meta) return null;
  const stale = meta.freshness_hours > 12;
  return <div className={meta.synthetic ? "notice notice-demo" : stale ? "notice notice-stale" : "notice"}>
    <Database size={17} /><div><strong>{meta.synthetic ? "Validated development dataset" : stale ? "Provider release is stale" : "Validated provider release"}</strong><span>{stale ? `The last validated release is ${Math.round(meta.freshness_hours)} hours old. Serving it while ingestion recovers.` : meta.warnings[0] ?? `Release ${meta.release_id}`}</span></div>
  </div>;
}

export function SectionHeading({ kicker, title, description, action }: { kicker?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="section-heading"><div>{kicker && <span className="eyebrow">{kicker}</span>}<h2>{title}</h2>{description && <p>{description}</p>}</div>{action}</div>;
}

export function MetricCard({ label, value, detail, change, tone = "cyan" }: { label: string; value: string; detail: string; change?: number; tone?: string }) {
  return <article className={`metric-card tone-${tone}`}><div className="metric-top"><span>{label}</span><span className="metric-spark" /></div><strong>{value}</strong><div className="metric-detail"><span>{detail}</span>{change !== undefined && <span className={change >= 0 ? "change up" : "change down"}>{change >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}{Math.abs(change)}%</span>}</div></article>;
}

export function Panel({ title, subtitle, children, className = "" }: { title?: string; subtitle?: string; children: ReactNode; className?: string }) {
  return <section className={`panel ${className}`}>{(title || subtitle) && <div className="panel-heading"><div>{title && <h3>{title}</h3>}{subtitle && <p>{subtitle}</p>}</div></div>}<div className="panel-body">{children}</div></section>;
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="empty-state"><div className="empty-orbit"><span /></div><strong>{title}</strong><p>{detail}</p></div>;
}
