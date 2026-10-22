import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { apiGet } from "../api";
import { ErrorState, LoadingState, Panel, SectionHeading } from "../components/Common";
import type { Workspace } from "../types";

export function SharedWorkspacePage() {
  const { token } = useParams();
  const query = useQuery({
    queryKey: ["shared-workspace", token],
    queryFn: () => apiGet<Workspace>(`/shared/${token}`),
    enabled: Boolean(token),
  });
  if (query.isLoading) return <LoadingState />;
  if (query.error || !query.data) return <ErrorState message="This share link is invalid or has been revoked." />;
  const workspace = query.data.data;
  return <div className="page-stack"><SectionHeading kicker="Read-only workspace" title={workspace.name} description="This unlisted view cannot be edited. Its owner can revoke access at any time." /><Panel title="Research notes"><p className="workspace-notes">{workspace.notes || "No notes were saved."}</p></Panel><Panel title="Saved analytical state"><div className="detail-metrics">{[["Primary date", workspace.state.primary_date], ["Comparison date", workspace.state.comparison_date ?? "None"], ["Rendering mode", workspace.state.rendering_mode], ["Selected objects", String(workspace.state.selected_objects.length)]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div></Panel></div>;
}
