import { Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CSSProperties } from "react";
import type { ConcentrationCell, DistributionBin, PersistencePoint, TimelinePoint } from "../types";

const COLORS = ["#55d6be", "#f5a65b", "#ef6f6c", "#7aa2f7", "#9d7fea"];

export function PopulationChart({ data, compact = false }: { data: TimelinePoint[]; compact?: boolean }) {
  const shown = compact ? data.filter((_, index) => index % 3 === 0 || index === data.length - 1) : data;
  return <div className={compact ? "chart chart-compact" : "chart"} aria-label="Orbital population timeline">
    <ResponsiveContainer width="100%" height="100%"><LineChart data={shown} margin={{ top: 10, right: 16, bottom: 0, left: -8 }}>
      <XAxis dataKey="date" tickFormatter={(value: string) => value.slice(0, 4)} tick={{ fill: "#8096aa", fontSize: 11 }} axisLine={false} tickLine={false} minTickGap={24} />
      <YAxis tick={{ fill: "#8096aa", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(value) => `${Math.round(Number(value) / 1000)}k`} />
      <Tooltip contentStyle={{ background: "#0e2132", border: "1px solid #254259", borderRadius: 10 }} labelFormatter={(value) => String(value).slice(0, 4)} />
      <Line type="monotone" dataKey="total" name="All tracked" stroke="#55d6be" strokeWidth={2.5} dot={false} />
      {!compact && <><Line type="monotone" dataKey="debris" name="Debris" stroke="#ef6f6c" strokeWidth={1.5} dot={false} /><Line type="monotone" dataKey="active_payload" name="Active payloads" stroke="#7aa2f7" strokeWidth={1.5} dot={false} /><Legend /></>}
    </LineChart></ResponsiveContainer>
  </div>;
}

export function CompositionChart({ data }: { data: DistributionBin[] }) {
  return <div className="chart chart-donut"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data} dataKey="count" nameKey="label" innerRadius="56%" outerRadius="82%" paddingAngle={2}>{data.map((item, index) => <Cell key={item.label} fill={COLORS[index % COLORS.length]} />)}</Pie><Tooltip contentStyle={{ background: "#0e2132", border: "1px solid #254259", borderRadius: 10 }} /><Legend iconType="circle" /></PieChart></ResponsiveContainer></div>;
}

export function ConcentrationHeatmap({ data }: { data: ConcentrationCell[] }) {
  const cells = data.filter((cell) => cell.altitude_start_km < 2000);
  const max = Math.max(...cells.map((cell) => cell.count), 1);
  return <div className="heatmap-wrap"><div className="heatmap-y">Altitude</div><div className="heatmap" role="img" aria-label="Altitude by inclination concentration heatmap">
    {cells.map((cell) => <div key={`${cell.altitude_start_km}-${cell.inclination_start_deg}`} className="heat-cell" title={`${cell.altitude_start_km}–${cell.altitude_end_km} km · ${cell.inclination_start_deg}–${cell.inclination_end_deg}° · ${cell.count} objects`} style={{ "--heat": String(cell.count / max) } as CSSProperties} />)}
  </div><div className="heatmap-x">Inclination 0° → 180°</div><div className="heat-legend"><span>Low</span><i /><span>High</span></div></div>;
}

export function PersistenceChart({ data }: { data: PersistencePoint[] }) {
  const colors: Record<string, string> = { active_payload: "#55d6be", inactive_payload: "#f5a65b", debris: "#ef6f6c", rocket_body: "#7aa2f7", unknown: "#9d7fea" };
  const rows = Array.from(new Set(data.map((point) => point.months))).map((months) => ({ months, ...Object.fromEntries(data.filter((point) => point.months === months).map((point) => [point.category, point.survival_probability])) }));
  return <div className="chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={rows} margin={{ top: 8, right: 18, left: 0, bottom: 0 }}><XAxis dataKey="months" tick={{ fill: "#8096aa", fontSize: 11 }} axisLine={false} /><YAxis domain={[0, 1]} tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`} tick={{ fill: "#8096aa", fontSize: 11 }} axisLine={false} /><Tooltip contentStyle={{ background: "#0e2132", border: "1px solid #254259", borderRadius: 10 }} /><Legend />{Object.entries(colors).map(([key, color]) => <Line key={key} type="stepAfter" dataKey={key} name={key.replaceAll("_", " ")} stroke={color} dot={false} strokeWidth={2} />)}</LineChart></ResponsiveContainer></div>;
}
