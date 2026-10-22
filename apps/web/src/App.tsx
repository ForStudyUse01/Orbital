import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { LoadingState } from "./components/Common";

const OverviewPage = lazy(() => import("./pages/OverviewPage").then((module) => ({ default: module.OverviewPage })));
const EnvironmentPage = lazy(() => import("./pages/EnvironmentPage").then((module) => ({ default: module.EnvironmentPage })));
const EvolutionPage = lazy(() => import("./pages/EvolutionPage").then((module) => ({ default: module.EvolutionPage })));
const DistributionPage = lazy(() => import("./pages/DistributionPage").then((module) => ({ default: module.DistributionPage })));
const ConcentrationPage = lazy(() => import("./pages/ConcentrationPage").then((module) => ({ default: module.ConcentrationPage })));
const EventsPage = lazy(() => import("./pages/EventsPage").then((module) => ({ default: module.EventsPage })));
const PersistencePage = lazy(() => import("./pages/PersistencePage").then((module) => ({ default: module.PersistencePage })));
const ObjectsPage = lazy(() => import("./pages/ObjectsPage").then((module) => ({ default: module.ObjectsPage })));
const MethodologyPage = lazy(() => import("./pages/MethodologyPage").then((module) => ({ default: module.MethodologyPage })));
const EventDetailPage = lazy(() => import("./pages/EventDetailPage").then((module) => ({ default: module.EventDetailPage })));
const ObjectDetailPage = lazy(() => import("./pages/ObjectDetailPage").then((module) => ({ default: module.ObjectDetailPage })));
const WorkspacesPage = lazy(() => import("./pages/WorkspacesPage").then((module) => ({ default: module.WorkspacesPage })));
const SharedWorkspacePage = lazy(() => import("./pages/SharedWorkspacePage").then((module) => ({ default: module.SharedWorkspacePage })));

export default function App() {
  return <Suspense fallback={<LoadingState />}><Routes><Route element={<Layout />}><Route index element={<OverviewPage />} /><Route path="environment" element={<EnvironmentPage />} /><Route path="evolution" element={<EvolutionPage />} /><Route path="distribution" element={<DistributionPage />} /><Route path="concentration" element={<ConcentrationPage />} /><Route path="events" element={<EventsPage />} /><Route path="events/:eventId" element={<EventDetailPage />} /><Route path="persistence" element={<PersistencePage />} /><Route path="objects" element={<ObjectsPage />} /><Route path="objects/:noradId" element={<ObjectDetailPage />} /><Route path="workspaces" element={<WorkspacesPage />} /><Route path="shared/:token" element={<SharedWorkspacePage />} /><Route path="methodology" element={<MethodologyPage />} /><Route path="*" element={<Navigate to="/" replace />} /></Route></Routes></Suspense>;
}
