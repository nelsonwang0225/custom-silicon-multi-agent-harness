import { caseNames } from "./experience-model";
import { deliveryCasePath, deliveryAttention } from "./delivery-case";
import { qualityCasePath, qualityAttention } from "./quality-case";
import { standardCasePath, standardAttention } from "./standard-case";
import { downstreamLabel, evidenceDecisionPath } from "./physical-validation";
import type { HostCase } from "./host";
import {
  connectedCasePath,
  decisionPath,
  executionLabel,
  reviewable,
} from "./host";
import type { SearchRecord, SourceAlert } from "./presentation-model";
export function hostSearch(data: HostCase | null): SearchRecord[] {
  if (!data) return [];
  const mode =
    data.mode === "deterministic_test"
      ? "Connected · Deterministic test double"
      : "Connected · Recorded host result";
  const records: SearchRecord[] = [
    ...(data.delivery
      ? [
          {
            id: "delivery/DR-009",
            title: "DR-009 · Delivery readiness",
            group: "Connected cases",
            context: data.delivery.status,
            mode,
            terms: `DR-009 ${data.delivery.context?.request.order_id || ""} ${data.delivery.context?.request.line_id || ""} ${data.delivery.context?.material.map((m) => m.lot_id).join(" ") || ""} Helios delivery commitment`,
            to: deliveryCasePath,
          },
        ]
      : []),
    ...(data.delivery?.records
      ? [
          ...data.delivery.records.plans,
          ...data.delivery.records.decisions,
          ...data.delivery.records.commitments,
          ...data.delivery.records.links,
        ].map((r) => ({
          id: r.id,
          title: r.id,
          group: "Delivery commitment records",
          context: "DR-009 · Source-owned record",
          mode,
          terms: `${r.id} DR-009 delivery proposal commitment decision`,
          to: deliveryCasePath,
        }))
      : []),
    ...(data.quality
      ? [
          {
            id: "quality/QE-004",
            title: "QE-004 · Yield / Quality Exception",
            group: "Connected cases",
            context: data.quality.status,
            mode,
            terms: `QE-004 ${data.quality.context?.exception.lot_id || ""} quality investigation Helios PRG-A17`,
            to: qualityCasePath,
          },
        ]
      : []),
    ...(data.quality?.records
      ? [
          ...data.quality.records.investigations,
          ...data.quality.records.plans,
          ...data.quality.records.decisions,
          ...data.quality.records.tasks,
        ].map((r) => ({
          id: r.id,
          title: r.id,
          group: "Quality recovery records",
          context: "QE-004 · Source-owned record",
          mode,
          terms: `${r.id} QE-004 quality investigation recovery plan decision task`,
          to: qualityCasePath,
        }))
      : []),
    ...(data.quality?.context?.evidence || []).map((e) => ({
      id: `quality-evidence/${e.id}`,
      title: String(e.id),
      group: "Quality evidence",
      context: "QE-004 · Historical evidence",
      mode,
      terms: `QE-004 ${e.id} evidence`,
      to: qualityCasePath,
    })),
    ...(data.standard
      ? [
          {
            id: "standard/CR-019",
            title: "CR-019 · Standard validation package",
            group: "Connected cases",
            context: data.standard.status,
            mode,
            terms:
              "CR-019 standard touchless approved profile Helios Validation Operations",
            to: standardCasePath,
          },
        ]
      : []),
    ...(data.standard?.handoffs || [])
      .flatMap((h) => [
        ...(h.package
          ? [
              {
                id: h.package.package_id,
                title: h.package.package_id,
                group: "Handoff packages",
                context: "CR-019 · Standard package",
                mode,
                terms: `${h.package.package_id} CR-019 standard handoff package ${h.package.procedure_id}`,
                to: standardCasePath,
              },
            ]
          : []),
        ...(h.intake
          ? [
              {
                id: h.intake.id,
                title: h.intake.id,
                group: "Validation Operations intakes",
                context: h.intake.downstream_owner,
                mode,
                terms: `${h.intake.id} CR-019 intake Validation Operations`,
                to: `/validation/intakes/${encodeURIComponent(h.intake.id)}`,
              },
            ]
          : []),
      ])
      .filter((v, i, a) => a.findIndex((x) => x.id === v.id) === i),
    ...[
      ...data.runs,
      ...(data.standard?.runs || []),
      ...(data.quality?.runs || []),
      ...(data.autonomous_quality?.runs || []),
      ...(data.delivery?.runs || []),
    ].map((r) => ({
      id: r.run_id,
      title: `${r.change_id} · Investigation · ${r.started_at.slice(0, 10)}`,
      group: "Recorded runs",
      context: `${r.change_id || "CR-017"} · ${r.status}`,
      mode: r.execution_mode === "live_model" ? "Live AI · Recorded run" : "Scripted demo · Recorded run",
      terms: `${r.run_id} ${r.change_id || "CR-017"} PRG-A17 investigation ${r.status} ${r.policy_route || ""}`,
      to: `/control/runs/${encodeURIComponent(r.run_id)}`,
    })),
    ...(data.automations || []).map((a) => ({
      id: a.automation_id,
      title: a.name,
      group: "Automation configurations",
      context: a.trigger_summary,
      mode: `${a.configuration_state} · Configuration preview`,
      terms: `${a.name} ${a.automation_id} ${a.workflow_name} ${a.program_id} ${a.case_scope || ""} ${a.trigger_summary}`,
      to: `/control/automations/${encodeURIComponent(a.automation_id)}`,
    })),
    ...data.proposals.map((p) => ({
      id: p.proposal.proposal_digest,
      title: `CR-017 · Proposal v${p.proposal.proposal_version}`,
      group: "Proposals & decisions",
      context: executionLabel(p),
      mode,
      terms: `${p.proposal.proposal_id} ${p.review?.source_decision_id || ""} ${p.proposal.proposal_digest} CR-017 proposal decision ${p.proposal.rationale}`,
      to: decisionPath(p),
    })),
  ];
  return [
    ...records.filter((r) => r.group !== "Connected cases"),
    ...(data.case_summaries || []).map((c) => ({
      id: `case/${c.program_id}/${c.change_id}`,
      title: `${c.change_id} · ${caseNames[c.change_id] || c.title}`,
      group: "Cases",
      context: c.state_label,
      mode: "Current connected source",
      terms: `${c.change_id} ${c.title} ${c.program_id} ${c.customer_id} Helios ${c.detail} ${records.find((r) => r.group === "Connected cases" && r.to === c.href)?.terms || ""}`,
      to: c.href,
    })),
    ...(data.decision_summaries || []).map((d) => ({
      id: `decision/${d.change_id}/${d.id}`,
      title: `${d.change_id} · ${d.title}${d.version == null ? "" : ` v${d.version}`}`,
      group: "Human decisions",
      context: `${d.status} · ${d.reviewer || d.required_role}`,
      mode: d.current ? "Current source binding" : "Historical / stale",
      terms: `${d.id} ${d.digest} ${d.source_decision_id || ""} ${d.change_id} decision`,
      to: d.href,
    })),
    ...(data.downstream?.physical.result
      ? [
          {
            id: `physical/${data.downstream.physical.result.id}`,
            title: data.downstream.physical.result.id,
            group: "Evidence & knowledge",
            context: "CR-017 · Current Validation Lab result",
            mode: "Source record",
            terms: `${data.downstream.physical.result.id} CR-017 evidence`,
            to: `${connectedCasePath}?tab=evidence&evidence=${encodeURIComponent(data.downstream.physical.result.id)}`,
          },
        ]
      : []),
    ...[
      ...(data.quality?.context?.material || []),
      ...(data.delivery?.context?.material || []),
    ].map((m) => ({
      id: `material/${m.id}`,
      title: `${m.id} · ${m.lot_id}`,
      group: "Source records",
      context: `${m.disposition} · ${m.eligible_unallocated_quantity} eligible`,
      mode: "Manufacturing source",
      terms: `${m.id} ${m.lot_id} QE-004 DR-009 PRG-A17 inventory held`,
      to: `/manufacturing/lots/${encodeURIComponent(m.lot_id)}`,
    })),
  ];
}
export function hostAlerts(data: HostCase | null): SourceAlert[] {
  return (data?.case_summaries || [])
    .filter((c) => c.attention !== "none")
    .map((c) => ({
      id: c.issue_key,
      title: c.state_label,
      context: `${c.change_id} · ${c.detail}`,
      to: c.href,
      kind: "host",
      priority: c.priority,
      caseId: c.change_id,
    }));
}
