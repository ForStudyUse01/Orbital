export type ObjectCategory = "active_payload" | "inactive_payload" | "debris" | "rocket_body" | "unknown";
export type OrbitalRegime = "LEO" | "MEO" | "GEO" | "GTO_HEO" | "SUPER_GEO" | "OTHER";

export interface SourceCitation { name: string; url: string; role: string }
export interface Meta {
  release_id: string; generated_at: string; data_as_of: string; synthetic: boolean;
  freshness_hours: number; sources: SourceCitation[]; warnings: string[];
}
export interface Envelope<T> { data: T; meta: Meta }
export interface Overview {
  total_objects: number; active_payloads: number; inactive_payloads: number; debris: number;
  rocket_bodies: number; tracked_regimes: number; modeled_over_1cm: number; change_yoy_percent: number;
}
export interface TimelinePoint {
  date: string; total: number; active_payload: number; inactive_payload: number; debris: number;
  rocket_body: number; unknown: number;
}
export interface DistributionBin { label: string; count: number; share: number }
export interface ConcentrationCell {
  altitude_start_km: number; altitude_end_km: number; inclination_start_deg: number;
  inclination_end_deg: number; count: number; normalized_density: number;
}
export interface Position { norad_id: number; name?: string; epoch?: string; x: number; y: number; z: number; category: ObjectCategory; regime: OrbitalRegime }
export interface SnapshotManifest {
  snapshot_date: string; resolution: "annual" | "monthly" | "weekly" | "current";
  positions: Position[]; object_count: number; excluded_from_positioning: number;
  position_time?: string; coordinate_frame?: string;
}
export interface OrbitalObject {
  norad_id: number; name: string; international_designator: string; category: ObjectCategory;
  regime: OrbitalRegime; country: string; launch_date: string; decay_date?: string; altitude_km: number;
  perigee_km: number; apogee_km: number; inclination_deg: number; period_minutes: number;
  eccentricity: number; quality: "current" | "stale" | "metadata_only";
}
export interface OrbitalEvent {
  id: string; name: string; date: string; event_type: string; assessed_cause: string;
  parent_norad_ids: number[]; fragments_catalogued: number; fragments_remaining: number;
  altitude_km: number; inclination_deg: number; description: string; deep_replay: boolean;
}
export interface PersistencePoint {
  months: number; survival_probability: number; at_risk: number; category: ObjectCategory;
}
export interface WorkspaceState {
  primary_date: string; comparison_date: string | null; categories: ObjectCategory[]; regimes: OrbitalRegime[];
  selected_objects: number[]; selected_events: string[]; chart_order: string[];
  camera: Record<string, number>; rendering_mode: "objects" | "density";
}
export interface Workspace {
  id: string; owner_id: string; name: string; notes: string; state: WorkspaceState;
  created_at: string; updated_at: string; share_token?: string;
}
