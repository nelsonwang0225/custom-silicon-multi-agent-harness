import {
  casePath,
  programPath,
  words,
  type Snapshot,
  type Program,
} from "./data";
import { catalog, navigation } from "./catalog";
import { agentRoles } from "./agent-activity";
import { riskHealth, overviewMetrics } from "./overview-model";

// An explicit presentation scope; no URL filter can invisibly alter Overview.
export const overviewProgramIds = ["PRG-A17", "PRG-P01", "PRG-P02"];
export const overviewPrograms = (data: Snapshot) =>
  data.programs.filter((p) => overviewProgramIds.includes(p.id));
export function healthMix(programs: Program[]) {
  const mix = { onTrack: 0, atRisk: 0, unknown: 0 };
  for (const p of programs) {
    if (p.health === "on_track" || p.health === "completed") mix.onTrack++;
    else if (riskHealth.some((h) => h === p.health)) mix.atRisk++;
    else mix.unknown++;
  }
  return mix;
}
export function overviewSummary(data: Snapshot) {
  const programs = overviewPrograms(data),
    ids = new Set(programs.map((p) => p.id));
  const cases = scopedCases(data).filter((c) => ids.has(c.change.program_id));
  return {
    programs,
    cases,
    metrics: overviewMetrics(programs, cases),
    mix: healthMix(programs),
    gate: data.milestones
      .filter((m) => ids.has(m.program_id) && m.health !== "completed")
      .sort((a, b) => a.baseline_at.localeCompare(b.baseline_at))[0],
  };
}
// Defense in depth on metadata joins, in addition to the server's reader scope.
export function scopedCases(data: Snapshot) {
  return data.cases.filter((c) =>
    data.programs.some(
      (p) =>
        p.id === c.change.program_id && p.customer_id === c.change.customer_id,
    ),
  );
}
export type SearchRecord = {
  id: string;
  title: string;
  group: string;
  context: string;
  mode: string;
  terms: string;
  to?: string;
  agent?: string;
};
export function searchIndex(
  data: Snapshot | null,
  workflows = catalog,
): SearchRecord[] {
  const items: SearchRecord[] = navigation.map(([title, to]) => ({
    id: to,
    title,
    to,
    group: "Destinations",
    context: "Stratos workspace",
    mode: "Navigation",
    terms: title,
  }));
  items.push(
    ...workflows.map((c) => ({
      id: c.workflow_id,
      title: c.name,
      to: `/control/workflows/${c.workflow_id}`,
      group: "Workflows",
      context: c.mode,
      mode: `${c.mode} · Definition`,
      terms: `${c.workflow_id} ${c.name} ${c.purpose}`,
    })),
  );
  items.push(
    ...agentRoles.map((r) => ({
      id: r.id,
      title: r.name,
      agent: r.id,
      group: "Agents",
      context: "Role definition",
      mode: "Preview",
      terms: `${r.id} ${r.name} ${r.capability}`,
    })),
  );
  if (!data) return items;
  const programs = new Map(data.programs.map((p) => [p.id, p]));
  for (const p of data.programs)
    items.push({
      id: `program/${p.id}`,
      title: p.name || p.id,
      to: programPath(p.id),
      group: "Programs & customers",
      context: `${p.id} · ${p.customer_name}`,
      mode: "Source record",
      terms: `${p.id} ${p.name} ${p.customer_id} ${p.customer_name} ${p.owner}`,
    });
  for (const c of scopedCases(data)) {
    const p = programs.get(c.change.program_id)!;
    const context = `${p.name} · ${c.change.id}`,
      terms = `${p.id} ${p.name} ${p.customer_id} ${p.customer_name} ${c.change.id}`;
    items.push({
      id: `case/${p.id}/${c.change.id}`,
      title: `${c.change.id} · ${c.change.title}`,
      to: casePath(c),
      group: "Cases",
      context: p.name || p.id,
      mode: "Source record",
      terms: `${terms} ${c.change.title} ${c.change.category}`,
    });
    for (const plan of c.change.plans.filter(
      (plan) => plan.program_id === p.id && plan.customer_id === p.customer_id,
    )) {
      const to = `${casePath(c)}?tab=options`;
      items.push({
        id: `plan/${p.id}/${plan.id}`,
        title: plan.id,
        to,
        group: "Plans & decisions",
        context,
        mode: `Recorded plan · ${words(plan.state)}`,
        terms: `${terms} ${plan.id} ${plan.state}`,
      });
      if (plan.decision_id)
        items.push({
          id: `decision/${p.id}/${plan.decision_id}`,
          title: plan.decision_id,
          to,
          group: "Plans & decisions",
          context: `${context} · ${plan.id}`,
          mode: "Recorded decision reference",
          terms: `${terms} ${plan.id} ${plan.decision_id}`,
        });
    }
    for (const o of c.coverage.items.filter(
      (o) => o.result.program_id === p.id,
    ))
      items.push({
        id: `result/${p.id}/${c.change.id}/${o.result.id}`,
        title: o.result.id,
        to: `${casePath(c)}?tab=evidence&evidence=${encodeURIComponent(o.result.id)}`,
        group: "Evidence & knowledge",
        context,
        mode: "Recorded observation",
        terms: `${terms} ${o.result.id} ${o.result.configuration_id} ${o.result.workload_profile_id}`,
      });
  }
  for (const d of data.documents.filter((d) => programs.has(d.program_id))) {
    const p = programs.get(d.program_id)!;
    items.push({
      id: `document/${d.program_id}/${d.id}`,
      title: `${words(d.document_type)} · ${d.id}`,
      to: `/control/knowledge?document=${encodeURIComponent(d.id)}`,
      group: "Evidence & knowledge",
      context: p.name || p.id,
      mode: "Document metadata",
      terms: `${d.id} ${d.document_type.replaceAll("_", " ")} ${p.id} ${p.name} ${p.customer_name}`,
    });
  }
  return Array.from(new Map(items.map((i) => [i.id, i])).values());
}
export function matchSearch(items: SearchRecord[], query: string) {
  const tokens=query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const rank=(i:SearchRecord)=>i.group==="Cases" ? 0 : i.group==="Programs & customers" ? 1 : i.group==="Human decisions" ? 2 : ["Evidence & knowledge","Source records","Quality evidence"].includes(i.group) ? 3 : i.group.includes("run") || i.group.includes("Run") ? 8 : 5;
  return [...new Map(items.map(i=>[i.id,i])).values()].filter(i=>tokens.every(t=>`${i.title} ${i.context} ${i.terms}`.toLocaleLowerCase().includes(t)))
    .sort((a,b)=>rank(a)-rank(b));
}
export type SourceAlert = {
  caseId?: string;
  priority?: number;
  id: string;
  title: string;
  context: string;
  time?: string;
  to: string;
  kind: string;
};
export function sourceAlerts(data: Snapshot | null): SourceAlert[] {
  if (!data) return [];
  const alerts: SourceAlert[] = [];
  for (const c of scopedCases(data)) {
    if (["closed", "superseded"].includes(c.change.workflow_state)) continue;
    const p = data.programs.find((p) => p.id === c.change.program_id)!;
    const plan = c.change.plans.find((p) => p.id === c.change.current_plan_id);
    const kind =
      c.change.execution_state === "lab_scheduled_pending_planner"
        ? "planner"
        : plan?.state === "draft"
          ? "review"
          : !c.coverage.coverage_satisfied
            ? "evidence"
            : null;
    if (!kind) continue;
    const record = kind === "review" ? plan! : c.change;
    alerts.push({
      id: `${p.id}/${c.change.id}/${kind}/${record.id}@${record.content_version}`,
      title:
        kind === "planner"
          ? "Scheduled · Planner link missing"
          : kind === "review"
            ? "Source plan awaiting review"
            : "Requested evidence missing",
      context: `${p.name} · ${c.change.id}`,
      time: record.updated_at,
      to: `${casePath(c)}?tab=${kind === "review" ? "options" : kind === "evidence" ? "evidence" : "summary"}`,
      kind,
      caseId:c.change.id,
    });
  }
  return Array.from(new Map(alerts.map((a) => [a.id, a])).values()).sort(
    (a, b) =>
      (b.time || "").localeCompare(a.time || "") || a.id.localeCompare(b.id),
  );
}
