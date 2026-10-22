import { create } from "zustand";
import type { ObjectCategory, OrbitalRegime, WorkspaceState } from "./types";

interface ExplorerStore extends WorkspaceState {
  setPrimaryDate: (value: string) => void;
  setComparisonDate: (value: string | null) => void;
  toggleCategory: (value: ObjectCategory) => void;
  toggleRegime: (value: OrbitalRegime) => void;
  setRenderingMode: (value: "objects" | "density") => void;
  selectObject: (value: number) => void;
  hydrate: (value: WorkspaceState) => void;
  snapshot: () => WorkspaceState;
}

const defaults: WorkspaceState = {
  primary_date: "2026-09-01",
  comparison_date: "2020-01-01",
  categories: [], regimes: [], selected_objects: [], selected_events: [],
  chart_order: ["population", "composition", "regimes", "concentration"],
  camera: { x: 0, y: 0, z: 3.4 }, rendering_mode: "objects",
};

export const useExplorerStore = create<ExplorerStore>((set, get) => ({
  ...defaults,
  setPrimaryDate: (primary_date) => set({ primary_date }),
  setComparisonDate: (comparison_date) => set({ comparison_date }),
  toggleCategory: (value) => set((state) => ({ categories: state.categories.includes(value) ? state.categories.filter((item) => item !== value) : [...state.categories, value] })),
  toggleRegime: (value) => set((state) => ({ regimes: state.regimes.includes(value) ? state.regimes.filter((item) => item !== value) : [...state.regimes, value] })),
  setRenderingMode: (rendering_mode) => set({ rendering_mode }),
  selectObject: (value) => set({ selected_objects: [value] }),
  hydrate: (value) => set(value),
  snapshot: () => {
    const state = get();
    return { primary_date: state.primary_date, comparison_date: state.comparison_date, categories: state.categories, regimes: state.regimes, selected_objects: state.selected_objects, selected_events: state.selected_events, chart_order: state.chart_order, camera: state.camera, rendering_mode: state.rendering_mode };
  },
}));

