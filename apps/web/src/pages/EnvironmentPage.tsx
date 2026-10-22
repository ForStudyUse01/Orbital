import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CalendarDays, CircleGauge, Crosshair, Globe2, Layers3, Play, Rotate3D, Search, Sparkles, X } from "lucide-react";
import { type FormEvent, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiGet } from "../api";
import { ErrorState, LoadingState, SectionHeading } from "../components/Common";
import { OrbitalScene, type CameraPreset } from "../components/OrbitalScene";
import { useExplorerStore } from "../store";
import type { ObjectCategory, OrbitalRegime, Position, SnapshotManifest } from "../types";

const categories: { value: ObjectCategory; label: string }[] = [
  { value: "active_payload", label: "Active payload" },
  { value: "inactive_payload", label: "Inactive payload" },
  { value: "debris", label: "Debris" },
  { value: "rocket_body", label: "Rocket body" },
  { value: "unknown", label: "Unknown" },
];
const regimes: Array<OrbitalRegime | "ALL"> = ["ALL", "LEO", "MEO", "GEO", "GTO_HEO"];
const cameraViews: Array<{ value: CameraPreset; label: string }> = [
  { value: "globe", label: "Globe" }, { value: "leo", label: "LEO" }, { value: "polar", label: "Polar" }, { value: "system", label: "System" },
];

function vectorDetails(position?: Position) {
  if (!position) return undefined;
  const radius = Math.hypot(position.x, position.y, position.z);
  return {
    altitude: Math.max(0, (radius - 1) * 6378.137),
    latitude: Math.asin(position.y / radius) * 180 / Math.PI,
    longitude: Math.atan2(-position.z, position.x) * 180 / Math.PI,
    radius: radius * 6378.137,
  };
}

export function EnvironmentPage() {
  const { primary_date, categories: selectedCategories, toggleCategory, rendering_mode, setRenderingMode, setPrimaryDate } = useExplorerStore();
  const [regime, setRegime] = useState<OrbitalRegime | "ALL">("ALL");
  const [search, setSearch] = useState("");
  const [searchMessage, setSearchMessage] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();
  // The public provider can reject local requests. Keep the ordinary route usable
  // and require an explicit mode=current choice before requesting live data.
  const live = searchParams.get("mode") === "current";
  const setLive = (value: boolean) => setSearchParams({ mode: value ? "current" : "demo" }, { replace: true });
  const [refresh, setRefresh] = useState(true);
  const [menuOpen, setMenuOpen] = useState(true);
  const [focusMode, setFocusMode] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<Position>();
  const [simulationSpeed, setSimulationSpeed] = useState(1);
  const [autoRotate, setAutoRotate] = useState(false);
  const [showGuides, setShowGuides] = useState(false);
  const [showAtmosphere, setShowAtmosphere] = useState(true);
  const [showStars, setShowStars] = useState(false);
  const [cameraPreset, setCameraPreset] = useState<CameraPreset>("leo");
  const snapshot = useQuery({ queryKey: ["environment", live ? "current" : primary_date], queryFn: () => apiGet<SnapshotManifest>(live ? "/environment/current" : `/snapshots/${primary_date}/manifest`), staleTime: 60_000, refetchInterval: live && refresh ? 60_000 : false, retry: false, refetchOnWindowFocus: false });
  const positions = useMemo(() => {
    const allPositions = snapshot.data?.data.positions ?? [];
    return allPositions.filter((item) =>
      (!selectedCategories.length || selectedCategories.includes(item.category)) &&
      (regime === "ALL" || item.regime === regime),
    );
  }, [regime, selectedCategories, snapshot.data]);
  const currentSelection = positions.find((point) => point.norad_id === selectedPosition?.norad_id);
  const selectedDetails = vectorDetails(currentSelection);
  const categoryCounts = useMemo(() => {
    const counts: Partial<Record<ObjectCategory, number>> = {};
    for (const point of positions) counts[point.category] = (counts[point.category] ?? 0) + 1;
    return counts;
  }, [positions]);

  if (snapshot.isPending) return <LoadingState label={live ? "Loading current CelesTrak satellite elements (first download may take 45 seconds)" : "Constructing demo snapshot"} />;
  if (!snapshot.data) return <div className="page-stack"><ErrorState message={live ? "The live provider is unavailable and no cached catalog is available. No synthetic data has been substituted." : "The requested demo snapshot is unavailable."} /><button className="button" onClick={() => { void snapshot.refetch(); }}>Retry connection</button><button className="button" onClick={() => setLive(!live)}>{live ? "Open clearly labeled demo history" : "Try current data"}</button></div>;
  const manifest = snapshot.data.data;

  const handleSearch = (event: FormEvent) => {
    event.preventDefault();
    const catalogId = Number(search.trim());
    const match = positions.find((position) => position.norad_id === catalogId || Boolean(search.trim() && position.name?.toLowerCase().includes(search.trim().toLowerCase())));
    if (!match) {
      setSearchMessage("No match in the visible population. Check your filters.");
      return;
    }
    setSelectedPosition(match);
    setSearchMessage(`NORAD ${match.norad_id} selected`);
    setCameraPreset(match.regime === "LEO" ? "leo" : "system");
  };

  return <div className={`page-stack environment-page ${focusMode ? "environment-focus" : ""}`}>
    <SectionHeading kicker="Orbital observatory" title="Explore the space around Earth" description="Current orbital estimates and a separate demo history. Drag to explore; use focus mode for an unobstructed globe." />
    <div className="environment-toolbar">
      <div className="segmented"><button className={live ? "active" : ""} onClick={() => { setLive(true); setSelectedPosition(undefined); }}>Current · CelesTrak</button><button className={!live ? "active" : ""} onClick={() => { setLive(false); setSelectedPosition(undefined); }}>Demo history</button></div>
      {!live && <label><CalendarDays size={16} /><span>Demo date</span><input type="date" min="1957-01-01" max="2026-09-21" value={primary_date} onChange={(event) => { setPrimaryDate(event.target.value); setSelectedPosition(undefined); }} /></label>}
      <div className="segmented"><button className={rendering_mode === "objects" ? "active" : ""} onClick={() => setRenderingMode("objects")}><Rotate3D size={15} />Objects</button><button className={rendering_mode === "density" ? "active" : ""} onClick={() => setRenderingMode("density")}><Layers3 size={15} />Density glow</button></div>
      <div className="filter-chips">{categories.map((category) => <button key={category.value} className={selectedCategories.includes(category.value) ? `chip active category-${category.value}` : `chip category-${category.value}`} onClick={() => toggleCategory(category.value)}>{category.label}</button>)}</div>
    </div>

    <div className="catalog-notice" role="status"><strong>{live ? "Real source · active satellite subset" : "Synthetic demonstration · not observed history"}</strong><span>{live ? `Source downloaded ${new Date(snapshot.data.meta.data_as_of).toLocaleString()} · ${snapshot.data.meta.freshness_hours.toFixed(1)} h old` : "Historical analytics have not yet been connected to provider archives."}</span>{snapshot.data.meta.warnings.map((warning) => <small key={warning}>{warning}</small>)}{snapshot.isError && <small>Refresh failed. Showing the last successful response.</small>}</div>
    <div className="environment-stage">
      <OrbitalScene positions={positions} selectedId={selectedPosition?.norad_id} onSelect={setSelectedPosition} renderingMode={rendering_mode} autoRotate={autoRotate} showGuides={showGuides} showAtmosphere={showAtmosphere} showStars={showStars} simulationSpeed={simulationSpeed} cameraPreset={cameraPreset} />

      {currentSelection && selectedDetails && <aside className="object-preview-card" aria-label={`Selected object ${currentSelection.norad_id}`}>
        <button className="object-preview-close" onClick={() => setSelectedPosition(undefined)} aria-label="Close object information"><X size={15} /></button>
        <span className="object-preview-kicker">Selected orbital object</span>
        <strong>{currentSelection.name ?? `NORAD ${currentSelection.norad_id}`}</strong>
        <small>NORAD {currentSelection.norad_id}</small>
        <dl>
          <div><dt>Type</dt><dd>{currentSelection.category.replaceAll("_", " ")}</dd></div>
          <div><dt>Regime</dt><dd>{currentSelection.regime.replace("GTO_HEO", "GTO/HEO")}</dd></div>
          <div><dt>Altitude</dt><dd>{selectedDetails.altitude.toFixed(0)} km</dd></div>
          <div><dt>{live ? "Longitude" : "Vector angle"}</dt><dd>{selectedDetails.longitude.toFixed(1)}°</dd></div>
        </dl>
        <Link to={`/objects/${currentSelection.norad_id}?source=${live ? "current" : "demo"}`}>View full details <ArrowRight size={14} /></Link>
      </aside>}

      <div className="scene-actions"><button onClick={() => setMenuOpen(!menuOpen)} aria-expanded={menuOpen}>{menuOpen ? "Hide controls" : "Show controls"}</button><button onClick={() => setFocusMode(!focusMode)}>{focusMode ? "Exit focus" : "Focus view"}</button></div>
      {menuOpen && <aside className="scene-control-panel" aria-label="Environment controls">
        <form className="scene-search" onSubmit={handleSearch}><Search size={14} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Satellite name or NORAD ID" aria-label="Satellite name or NORAD ID" /><button type="submit">Find</button></form>
        {searchMessage && <p className="search-message">{searchMessage}</p>}
        <div className="control-section"><div className="control-heading"><Play size={13} /><span>Camera rotation speed</span><b>{simulationSpeed.toFixed(1)}×</b></div><input className="speed-range" aria-label="Camera rotation speed" type="range" min="0" max="4" step="0.5" value={simulationSpeed} onChange={(event) => setSimulationSpeed(Number(event.target.value))} /></div>
        <div className="control-section"><span className="control-label">Scene layers</span>
          <label className="scene-switch"><span>Rotate camera</span><input type="checkbox" checked={autoRotate} onChange={(event) => setAutoRotate(event.target.checked)} /></label>
          {live && <label className="scene-switch"><span>Auto refresh · 60 seconds</span><input type="checkbox" checked={refresh} onChange={(event) => setRefresh(event.target.checked)} /></label>}
          <label className="scene-switch"><span>Orbital guides</span><input type="checkbox" checked={showGuides} onChange={(event) => setShowGuides(event.target.checked)} /></label>
          <label className="scene-switch"><span>Atmosphere</span><input type="checkbox" checked={showAtmosphere} onChange={(event) => setShowAtmosphere(event.target.checked)} /></label>
          <label className="scene-switch"><span>Deep-space stars</span><input type="checkbox" checked={showStars} onChange={(event) => setShowStars(event.target.checked)} /></label>
        </div>
        <div className="control-section"><span className="control-label">Camera view</span><div className="view-grid">{cameraViews.map((view) => <button key={view.value} className={cameraPreset === view.value ? "active" : ""} onClick={() => setCameraPreset(view.value)}>{view.label}</button>)}</div></div>
        <div className="control-section"><span className="control-label">Orbital regime</span><div className="regime-filter">{regimes.map((item) => <button key={item} className={regime === item ? "active" : ""} onClick={() => { setRegime(item); setSelectedPosition(undefined); }}>{item.replace("GTO_HEO", "GTO/HEO")}</button>)}</div></div>
      </aside>}

      <aside className="scene-legend-panel" aria-label="Object type legend"><span>Visible object types</span>{categories.map((item) => <div key={item.value}><i className={`legend-dot category-${item.value}`} /><b>{item.label}</b><small>{(categoryCounts[item.value] ?? 0).toLocaleString()}</small></div>)}</aside>
      <div className="scene-status"><span>{manifest.position_time ? new Date(manifest.position_time).toISOString().replace("T", " ").slice(0, 19) : `${manifest.snapshot_date} 00:00:00`} UTC</span><b>{positions.length.toLocaleString()} objects displayed · {live ? "SGP4 estimate" : "Demo"}</b></div>
    </div>

    <div className="environment-detail-grid">
      <article className="environment-card selected-object-card">
        <div className="card-title"><Crosshair size={16} /><div><span>Selected vector</span><strong>{currentSelection ? `${currentSelection.name ?? "NORAD"} ${currentSelection.norad_id}` : "Select an orbital point"}</strong></div></div>
        {currentSelection && selectedDetails ? <div className="vector-metrics"><div><span>Class</span><b>{currentSelection.category.replaceAll("_", " ")}</b></div><div><span>Regime</span><b>{currentSelection.regime.replace("GTO_HEO", "GTO/HEO")}</b></div><div><span>Altitude</span><b>{selectedDetails.altitude.toFixed(0)} km</b></div><div><span>Geocentric radius</span><b>{selectedDetails.radius.toFixed(0)} km</b></div><div><span>{live ? "Geocentric latitude" : "Vector latitude"}</span><b>{selectedDetails.latitude.toFixed(2)}°</b></div><div><span>{live ? "Longitude" : "Vector azimuth"}</span><b>{selectedDetails.longitude.toFixed(2)}°</b></div></div> : <p>Click a rendered point or enter a NORAD catalog ID to inspect its snapshot vector. Coordinates are geocentric estimates, not a navigation solution.</p>}
      </article>
      <article className="environment-card earth-card"><div className="card-title"><Globe2 size={16} /><div><span>Reference planet</span><strong>Earth</strong></div></div><div className="planet-facts"><div><span>Equatorial radius</span><b>6,378.137 km</b></div><div><span>Axial tilt</span><b>23.44°</b></div><div><span>Sidereal rotation</span><b>23 h 56 m</b></div><div><span>Kármán line</span><b>100 km</b></div></div><p>Photographic day and night imagery with real cloud cover, coastlines and city lights, lit from a fixed sun direction so the terminator falls where it would in daylight. The atmospheric rim is illustrative.</p></article>
      <article className="environment-card scene-summary-card"><div className="card-title"><CircleGauge size={16} /><div><span>Scene summary</span><strong>{manifest.resolution} resolution</strong></div></div><div className="summary-row"><Sparkles size={14} /><span>Dataset</span><b>{manifest.object_count.toLocaleString()}</b></div><div className="summary-row"><Layers3 size={14} /><span>Positioned</span><b>{(manifest.object_count - manifest.excluded_from_positioning).toLocaleString()}</b></div><div className="summary-row"><Globe2 size={14} /><span>Coordinate frame</span><b>{manifest.coordinate_frame ?? "Demo geocentric"}</b></div><p>Markers are intentionally enlarged. Shell guides aid orientation and do not represent protected zones or collision risk.</p></article>
    </div>
  </div>;
}
