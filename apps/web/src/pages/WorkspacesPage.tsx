import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Save, Share2, Trash2 } from "lucide-react";
import { useState } from "react";
import { apiGet, apiSend } from "../api";
import { LoadingState, Panel, SectionHeading } from "../components/Common";
import { useExplorerStore } from "../store";
import type { Workspace } from "../types";

export function WorkspacesPage() {
  const state = useExplorerStore((store) => store.snapshot);
  const hydrate = useExplorerStore((store) => store.hydrate);
  const [name, setName] = useState("Orbital environment study");
  const [notes, setNotes] = useState("Compare concentration change and event persistence.");
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["workspaces"], queryFn: () => apiGet<Workspace[]>("/workspaces") });
  const create = useMutation({ mutationFn: () => apiSend<Workspace>("/workspaces", "POST", { name, notes, state: state() }), onSuccess: () => client.invalidateQueries({ queryKey: ["workspaces"] }) });
  const remove = useMutation({ mutationFn: (id: string) => apiSend(`/workspaces/${id}`, "DELETE"), onSuccess: () => client.invalidateQueries({ queryKey: ["workspaces"] }) });
  const share = useMutation({ mutationFn: (id: string) => apiSend<Workspace>(`/workspaces/${id}/share`, "POST"), onSuccess: () => client.invalidateQueries({ queryKey: ["workspaces"] }) });
  if (query.isLoading) return <LoadingState />;
  return <div className="page-stack"><SectionHeading kicker="Saved research" title="Return to an analytical point of view" description="Save filters, comparison dates, 3D mode, object selections and research notes." /><div className="workspace-grid"><Panel title="New workspace" subtitle="Captures the current explorer state"><form className="workspace-form" onSubmit={(event) => { event.preventDefault(); create.mutate(); }}><label>Name<input value={name} onChange={(event) => setName(event.target.value)} maxLength={120} /></label><label>Notes<textarea value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={20000} rows={6} /></label><button className="button button-primary" disabled={create.isPending}><Save size={16} />{create.isPending ? "Saving…" : "Save current view"}</button></form></Panel><Panel title="Your workspaces" subtitle="Private until you create a share link" className="span-2"><div className="workspace-list">{query.data!.data.length === 0 && <p className="muted">No saved workspaces yet.</p>}{query.data!.data.map((workspace) => <article key={workspace.id}><div><strong>{workspace.name}</strong><span>{workspace.notes}</span><small>Updated {new Date(workspace.updated_at).toLocaleString()}</small></div><div className="workspace-actions"><button className="icon-button" onClick={() => hydrate(workspace.state)} title="Restore workspace"><Copy size={16} /></button><button className="icon-button" onClick={() => share.mutate(workspace.id)} title="Create new share link"><Share2 size={16} /></button><button className="icon-button danger" onClick={() => remove.mutate(workspace.id)} title="Delete workspace"><Trash2 size={16} /></button></div>{workspace.share_token && <code>{`${location.origin}/shared/${workspace.share_token}`}</code>}</article>)}</div></Panel></div></div>;
}
