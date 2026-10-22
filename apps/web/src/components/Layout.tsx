import {
  Activity, Atom, BookOpen, Boxes, CircleDotDashed, Clock3, Database, Globe2,
  LayoutDashboard, Menu, Orbit, PanelLeftClose, Save, Search, Sparkles, X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useMemo, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

type NavItem = readonly [label: string, path: string, icon: LucideIcon];
type NavGroup = { label: string; items: readonly NavItem[] };

const groups: readonly NavGroup[] = [
  { label: "Observe", items: [
    ["Overview", "/", LayoutDashboard], ["3D Environment", "/environment", Globe2], ["Objects", "/objects", Search],
  ] },
  { label: "Analyze", items: [
    ["Population", "/evolution", Activity], ["Distribution", "/distribution", Boxes], ["Concentration", "/concentration", CircleDotDashed],
    ["Events", "/events", Sparkles], ["Persistence", "/persistence", Clock3],
  ] },
  { label: "Research", items: [
    ["Workspaces", "/workspaces", Save], ["Methodology", "/methodology", BookOpen],
  ] },
];

export function Layout() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const current = groups.flatMap((group) => group.items).find((item) => item[1] === location.pathname)?.[0] ?? "Object intelligence";
  const today = useMemo(() => new Date().toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }), []);
  return <div className="app-shell">
    <aside className={`sidebar ${open ? "sidebar-open" : ""}`} aria-label="Primary navigation">
      <div className="brand-lockup">
        <div className="brand-mark"><Orbit size={22} /></div>
        <div><span className="eyebrow">Orbital</span><strong>Environment Intelligence</strong></div>
        <button className="icon-button mobile-only" onClick={() => setOpen(false)} aria-label="Close navigation"><X size={20} /></button>
      </div>
      <div className="catalog-status"><span className="live-dot" /><div><strong>Environment online</strong><span>Release demo-2026.09</span></div></div>
      <nav>
        {groups.map((group) => <div className="nav-group" key={group.label}>
          <span className="nav-label">{group.label}</span>
          {group.items.map(([label, path, Icon]) => <NavLink key={path} to={path} onClick={() => setOpen(false)} className={({ isActive }) => isActive ? "nav-item active" : "nav-item"} end={path === "/"}>
            <Icon size={18} /><span>{label}</span>
          </NavLink>)}
        </div>)}
      </nav>
      <div className="sidebar-foot"><Database size={16} /><span>Tracked ≠ total physical population</span></div>
    </aside>
    <main className="main-shell">
      <header className="topbar">
        <button className="icon-button mobile-menu" onClick={() => setOpen(true)} aria-label="Open navigation"><Menu size={20} /></button>
        <h1>{current}</h1>
        <div className="topbar-actions"><div className="data-pill"><Atom size={16} /><span>Data as of</span><strong>{today}</strong></div><div className="avatar" title="Local demo user">YD</div></div>
      </header>
      <div className="page-frame"><Outlet /></div>
    </main>
    {open && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setOpen(false)}><PanelLeftClose /></button>}
  </div>;
}
