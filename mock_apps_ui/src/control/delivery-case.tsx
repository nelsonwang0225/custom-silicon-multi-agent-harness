import { KnowledgeRunEvidence } from "./knowledge-runs";
import { workflowStep, traceStatus } from "./trace-language";
import { CaseHeader } from "./case-experience";
import { ActionAccess } from "./persona";
import { useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Link, AllowedAction, canAct } from "./access";
import { ArrowRight, Play } from "lucide-react";
import { useHost, type HostSchema } from "./host";
import { RuntimeLabel } from "./runtime-label";
import { words, date } from "./data";
import { Empty, Heading, Section, Facts, StatusText } from "./ui";
import { RunFindings } from "./connected-case";
export const deliveryCasePath = "/control/programs/PRG-A17/cases/DR-009";
export const deliveryAttention = (v: HostSchema["DeliveryCaseView"]) =>
  [
    "awaiting_review",
    "readiness_blocked",
    "outcome_unknown",
    "partial_completion",
    "failed",
    "verification_failed",
    "stale",
  ].includes(v.status) || v.runs?.[0]?.status === "failed";
export function DeliverySummary() {
  const v = useHost()?.data?.delivery;
  if (!v) return null;
  const a = v.context?.analysis;
  return (
    <Section
      title="DR-009 · Delivery readiness"
      note="Helios Atlas Inference · Connected"
    >
      <StatusText tone={deliveryAttention(v) ? "warning" : "neutral"}>
        {words(v.status)}
      </StatusText>
      <p>
        {a
          ? a.technical_readiness !== "READY"
            ? `Technical readiness ${words(a.technical_readiness)} · ${a.eligible_quantity} supply eligible`
            : `${a.customer_ready_quantity} / ${a.requested_quantity ?? "Unknown"} currently supportable · ${a.gap_quantity ?? "Unknown"} gap`
          : "Current source unavailable"}
      </p>
      <Link className="cp-text-link" to={deliveryCasePath}>
        Inspect delivery readiness <ArrowRight size={15} />
      </Link>
    </Section>
  );
}
export function DeliveryDecisions() {
  const v = useHost()?.data?.delivery;
  if (!v?.records?.plans.length) return null;
  return (
    <Section
      title="Delivery commitment decisions"
      note="Program Owner · Exact source quantity and date"
    >
      {v.records.plans.map((p) => (
        <article className="cp-record" key={p.id}>
          <strong>
            DR-009 · {p.quantity} units · {date(p.committed_at)}{" "}
            {p.date_semantics}
          </strong>
          <p>
            {v.records!.decisions.find((d) => d.plan_id === p.id)?.decision ||
              (v.status === "stale"
                ? "Source changed · Reassess"
                : "Program Owner review required")}
          </p>
          <Link to={`${deliveryCasePath}#decision`}>
            Review commitment · {p.id}
          </Link>
        </article>
      ))}
    </Section>
  );
}
export function DeliveryCase() {
  const host = useHost(),
    v = host?.data?.delivery;
  const [error, setError] = useState(""),
    [comment, setComment] = useState("");
  const lock = useRef(false);
  const [params] = useSearchParams();
  const selectedPlan = params.get("plan");
  if (!host || !v)
    return (
      <Empty>
        DR-009 source context is not available.{" "}
        <button onClick={() => void host?.refresh()}>Refresh</button>
      </Empty>
    );
  const c = v.context,
    a = c?.analysis,
    p = selectedPlan
      ? v.progress?.find((p) => p.plan_id === selectedPlan)
      : v.progress?.[0];
  const plan = v.records?.plans.find((x) => x.id === p?.plan_id),
    decision = v.records?.decisions.find((x) => x.plan_id === plan?.id);
  const current =
    !!c &&
    v.source_available &&
    !host.error &&
    v.status !== "stale" &&
    (!selectedPlan || !!p) &&
    v.runs?.find((r) => r.run_id === p?.run_id)?.business_outcome !== "stale";
  const busy =
    !!host.busy || (v.runs || []).some((r) => r.status === "running");
  const ref =
    p && plan
      ? {
          run_id: p.run_id,
          plan_id: plan.id,
          plan_version: plan.plan_version,
          plan_digest: plan.plan_digest,
        }
      : null;
  const action = async (path: string, body: unknown) => {
    if (lock.current) return;
    lock.current = true;
    setError("");
    try {
      await host.act(path, body);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      lock.current = false;
    }
  };
  const start = async () => {
    const key = "stratos.delivery.invocation";
    let id = sessionStorage.getItem(key);
    if (!id) {
      id = "ui_" + crypto.randomUUID().replaceAll("-", "");
      sessionStorage.setItem(key, id);
    }
    if (lock.current) return;
    lock.current = true;
    setError("");
    try {
      await host.act("/cases/DR-009/investigations", {
        invocation_id: id,
        change_id: "DR-009",
        workflow_id: "delivery_readiness",
      });
      sessionStorage.removeItem(key);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      lock.current = false;
    }
  };
  return (
    <div className="cp-case-page cp-case-delivery">
      <CaseHeader
        id="DR-009"
        title="Delivery readiness"
        action={
          <div className="cp-case-heading-actions">
            <AllowedAction caseId="DR-009" action="investigate">
              <button
                className={
                  plan &&
                  !decision &&
                  canAct(host.capabilities, "DR-009", "review")
                    ? "cp-button"
                    : "cp-primary"
                }
                disabled={
                  !c ||
                  !v.source_available ||
                  busy ||
                  !canAct(host.capabilities, "DR-009", "investigate")
                }
                onClick={() => void start()}
              >
                <Play size={15} />
                {v.runs?.some((r) => r.status === "running")
                  ? "Analyzing delivery readiness…"
                  : "Assess delivery readiness"}
              </button>
            </AllowedAction>
            {plan &&
              !decision &&
              canAct(host.capabilities, "DR-009", "review") && (
                <a className="cp-button cp-primary" href="#decision">
                  Review exact commitment <ArrowRight size={15} />
                </a>
              )}
          </div>
        }
      />
      {selectedPlan && !p && (
        <p className="cp-error" role="alert">
          This exact source plan is unavailable. No replacement has been
          selected.
        </p>
      )}
      <ActionAccess
        caseId="DR-009"
        action="investigate"
        ready={current && !busy}
        reason={
          busy
            ? "Investigation or action in progress."
            : "Refresh current sources before acting."
        }
      />
      <div className="cp-inline cp-case-command">
        <StatusText tone={deliveryAttention(v) ? "warning" : "neutral"}>
          {words(v.status)}
        </StatusText>
        <button onClick={() => void host.refresh()}>
          Refresh source state
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
      <RuntimeLabel caseId="DR-009" run={v.runs?.[0]} />
      {!current && (
        <p role="status">
          Current source authority is unavailable or stale. Reassess before
          review or execution.
        </p>
      )}
      {v.runs?.[0] && <RunFindings run={v.runs[0]} />}
      {c && a && (
        <>
          <details className="cp-secondary-content">
            <summary>Exact customer request</summary>
            <Section
              title="Exact customer request"
              note="Order demand, requested arrival and authorized release commitment are separate."
            >
              <Facts
                rows={[
                  [
                    "Customer / order line",
                    `${c.customer_id} · ${c.request.order_id} / ${c.request.line_id}`,
                  ],
                  [
                    "Requested",
                    `${c.request.quantity ?? "Unknown"} units · ${c.request.requested_at ? date(c.request.requested_at, true) : "Date missing"} · ${c.request.date_semantics}`,
                  ],
                  ["Destination", c.request.destination || "Unknown"],
                  [
                    "Original order date",
                    String(c.order.committed_delivery_at),
                  ],
                  [
                    "Required configuration",
                    `${c.request.configuration_id} · ${String(c.configuration.product_revision)} · ${String(c.configuration.firmware)} / ${String(c.configuration.runtime)}`,
                  ],
                ]}
              />
            </Section>
          </details>
          <Section
            title="Readiness gates"
            note="Technical clearance does not follow from physical inventory."
          >
            <Facts
              rows={[
                [
                  "Technical readiness",
                  `${a.technical_readiness} · ${a.technical_reasons.join(" · ")}`,
                ],
                [
                  "Engineering requirement / review",
                  `${c.request.requirement_revision_id} · ${c.request.technical_change_id ? `CR-017 ${String((c.technical_dependency?.physical as Record<string, unknown> | undefined)?.engineering_status || "pending")}` : `${c.clearance?.id || "Missing"} · ${c.clearance?.status || "Unknown"}`}`,
                ],
                [
                  "Validation evidence",
                  c.evidence.map((e) => String(e.id)).join(", ") || "Missing",
                ],
                [
                  "Quality",
                  `${a.held_quantity} held units excluded · Shared Manufacturing disposition`,
                ],
                [
                  "Supply / allocation",
                  `${a.eligible_quantity} eligible · ${a.allocated_quantity} allocated elsewhere`,
                ],
                [
                  "Timing",
                  `${words(a.timing_status)} · ${a.timing_reasons.join(" · ")}`,
                ],
                [
                  "Commercial authority",
                  decision?.decision === "approve"
                    ? "Exact Program Owner approval recorded"
                    : decision?.decision === "reject"
                      ? "Proposal rejected by Program Owner"
                      : "Exact Program Owner decision required",
                ],
              ]}
            />
            {a.blockers.length > 0 && (
              <p role="status">Proposal blocked: {a.blockers.join(" · ")}</p>
            )}
            {c.request.technical_change_id && (
              <Link to="/control/programs/PRG-A17/cases/CR-017">
                Inspect CR-017 technical dependency
              </Link>
            )}
          </Section>
          <details className="cp-secondary-content">
            <summary>Inventory & supportable quantity</summary>
            <Section
              title="Inventory & supportable quantity"
              note="Non-overlapping physical groups. Future receipts are shown separately."
            >
              <div className="cp-quality-quantities">
                {[
                  ["Physical inventory", a.physical_total],
                  ["Quality held", a.held_quantity],
                  ["Allocated elsewhere", a.allocated_quantity],
                  ["Wrong configuration", a.configuration_mismatch_quantity],
                  ["Eligible unallocated", a.eligible_quantity],
                  ["Customer ready", a.customer_ready_quantity],
                  [
                    "Requested / gap",
                    `${a.requested_quantity ?? "?"} / ${a.gap_quantity ?? "?"}`,
                  ],
                ].map(([label, value]) => (
                  <div key={label}>
                    <small>{label}</small>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
              <div
                className="cp-delivery-bar"
                role="img"
                aria-label={`${a.physical_total} physical: ${a.eligible_quantity} eligible, ${a.held_quantity} held, ${a.allocated_quantity} allocated elsewhere, ${a.configuration_mismatch_quantity} wrong configuration`}
              >
                {[
                  a.eligible_quantity,
                  a.held_quantity,
                  a.allocated_quantity,
                  a.configuration_mismatch_quantity,
                  a.other_unavailable_quantity,
                ].map((q, i) => (
                  <span
                    key={i}
                    style={{
                      width: `${a.physical_total ? (q / a.physical_total) * 100 : 0}%`,
                    }}
                  />
                ))}
              </div>
              <p>
                {a.full_request_supportable
                  ? "The requested quantity and timing are supportable, subject to exact commitment approval."
                  : "No currently supportable full-delivery commitment."}{" "}
                Held material and existing allocations remain governed.
              </p>
              <div className="cp-table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Source material / lot</th>
                      <th>Configuration</th>
                      <th>Disposition</th>
                      <th>Physical</th>
                      <th>Released</th>
                      <th>Held</th>
                      <th>Allocated</th>
                    </tr>
                  </thead>
                  <tbody>
                    {c.material.map((m) => (
                      <tr key={m.id}>
                        <td>
                          {m.id} · {m.lot_id}
                        </td>
                        <td>{m.configuration_id}</td>
                        <td>{words(m.disposition)}</td>
                        <td>{m.physical_quantity}</td>
                        <td>{m.released_quantity}</td>
                        <td>{m.held_quantity}</td>
                        <td>{m.allocated_quantity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Link to="/control/programs/PRG-A17/cases/QE-004">
                Inspect shared QE-004 material
              </Link>
            </Section>
          </details>
          <details className="cp-secondary-content">
            <summary>Timing & existing allocations</summary>
            <Section
              title="Timing & existing allocations"
              note="Material availability is not customer arrival."
            >
              <Facts
                rows={[
                  [
                    "Material ready",
                    c.logistics?.material_ready_at
                      ? date(c.logistics.material_ready_at, true)
                      : "Unknown",
                  ],
                  [
                    "Preparation / loading / transit",
                    c.logistics
                      ? `${c.logistics.preparation_minutes ?? "?"} / ${c.logistics.loading_minutes ?? "?"} / ${c.logistics.transit_minutes ?? "?"} minutes · ${c.logistics.state}`
                      : "Unknown",
                  ],
                  [
                    "Earliest shipment",
                    a.earliest_ship_at
                      ? date(a.earliest_ship_at, true)
                      : "Unknown",
                  ],
                  [
                    "Earliest arrival",
                    a.earliest_arrival_at
                      ? date(a.earliest_arrival_at, true)
                      : "Unknown",
                  ],
                  [
                    "Future expected supply",
                    `${a.future_expected_quantity} · Excluded from current eligible inventory`,
                  ],
                ]}
              />
              {c.allocations.map((x) => (
                <p key={x.id}>
                  {x.id} · {x.quantity} units for {x.order_id} ·{" "}
                  {x.release_reference}
                </p>
              ))}
              {c.future_supply.map((f) => (
                <p key={f.id}>
                  {f.id} · {f.quantity} expected · {words(f.status)} · Material
                  expected{" "}
                  {f.expected_at ? date(f.expected_at, true) : "Unknown"}.{" "}
                  {f.release_prerequisites.join(" · ")}. Arrival is not
                  guaranteed.
                </p>
              ))}
            </Section>
          </details>
          <Section
            title="Delivery options"
            note="Allocation review and future supply remain analysis-only."
          >
            <div className="cp-business-options" aria-label="Delivery options">
              {a.options.map((option, index) => (
                <article
                  className="cp-business-option"
                  key={option.id + index}
                  data-executable={option.executable}
                >
                  <div className="cp-option-top">
                    <StatusText tone={option.executable ? "agent" : "neutral"}>
                      {option.executable
                        ? "Available for exact review"
                        : "Analysis only"}
                    </StatusText>
                    <span>{option.owner}</span>
                  </div>
                  <h3>{words(option.id)}</h3>
                  <p>{option.effect}</p>
                  <div className="cp-option-bottom">
                    <strong>
                      {option.quantity} <small>units</small>
                    </strong>
                    <span>
                      {option.remaining_gap ?? "Unknown"} remaining gap
                    </span>
                  </div>
                  <p className="cp-option-date">
                    {option.proposed_at
                      ? date(option.proposed_at, true)
                      : "No supported date"}
                  </p>
                  <details>
                    <summary>Prerequisites, obligations & cost</summary>
                    <ul>
                      {option.prerequisites.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                    <p>{option.affected_obligations.join(" · ")}</p>
                    <p>
                      Cost:{" "}
                      {option.cost_cents == null
                        ? "Unknown"
                        : `$${option.cost_cents / 100}`}
                    </p>
                    <p>Decision authority: {words(option.required_role)}</p>
                  </details>
                </article>
              ))}
            </div>
          </Section>
        </>
      )}
      <div id="decision" />
      <Section
        title="Human commitment decision"
        note="Only the exact approved quantity/date may be written to ERP and linked in Planner."
      >
        {!plan ? (
          <Empty>
            {a?.proposal_allowed
              ? "Run analysis to prepare the source-bound proposal."
              : "Resolve the source readiness blockers before a commitment proposal."}
          </Empty>
        ) : (
          <>
            <div className="cp-exact-decision">
              <div>
                <span className="cp-story-kicker">
                  Exact delivery commitment
                </span>
                <h3>
                  {plan.quantity} units · {date(plan.committed_at, true)}
                </h3>
                <p>
                  {plan.date_semantics} · {plan.destination}
                </p>
                <StatusText tone="agent">
                  {plan.owner} · Program Owner decision
                </StatusText>
              </div>
              <div className="cp-decision-quantity">
                <strong>
                  {plan.analysis.requested_quantity! - plan.quantity}
                </strong>
                <span>units remain uncommitted</span>
              </div>
            </div>
            <div className="cp-decision-consequence">
              <strong>If approved</strong>
              <p>
                Record this exact delivery-release commitment in ERP and its
                matching Planner link. Allocation, lot release, shipment and
                acceptance remain separate.
              </p>
            </div>
            <details className="tr-details">
              <summary>Exact proposal reference</summary>
              <p>
                {plan.id} · Version {plan.plan_version}
              </p>
              <p className="cp-digest">
                Content fingerprint: {plan.plan_digest}
              </p>
            </details>
            {!decision && canAct(host.capabilities, "DR-009", "review") && (
              <>
                <label className="cp-decision-comment">
                  Review comment
                  <textarea
                    rows={3}
                    aria-label="Review comment"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    maxLength={1500}
                  />
                </label>
                <ActionAccess
                  caseId="DR-009"
                  action="review"
                  ready={current && !busy}
                  reason="Refresh current source records before deciding."
                />
                <div className="cp-inline">
                  {(["approve", "reject"] as const).map((d) => (
                    <AllowedAction key={d} caseId="DR-009" action="review">
                      <button
                        className={
                          d === "approve" ? "cp-primary" : "cp-reject-action"
                        }
                        disabled={
                          !current ||
                          busy ||
                          !canAct(host.capabilities, "DR-009", "review")
                        }
                        onClick={() =>
                          void action("/delivery-commitment/review", {
                            ...ref,
                            decision: d,
                            comment,
                          })
                        }
                      >
                        {d === "approve"
                          ? "Approve exact commitment"
                          : "Reject commitment"}
                      </button>
                    </AllowedAction>
                  ))}
                </div>
              </>
            )}
            {decision && (
              <p>
                {words(decision.decision)} · {decision.signer_identity} ·{" "}
                {decision.comment}
              </p>
            )}
            <ActionAccess
              caseId="DR-009"
              action="execute"
              ready={
                !!current &&
                decision?.decision === "approve" &&
                v.status !== "verified"
              }
              reason={
                v.status === "verified"
                  ? "ERP and Planner readback already verified. No further execution is needed."
                  : "A current exact Program Owner approval is required before execution."
              }
            />
            <AllowedAction caseId="DR-009" action="execute">
              <button
                className="cp-primary"
                disabled={
                  !current ||
                  busy ||
                  decision?.decision !== "approve" ||
                  v.status === "verified" ||
                  !canAct(host.capabilities, "DR-009", "execute")
                }
                onClick={() => void action("/delivery-commitment/execute", ref)}
              >
                {v.status === "partial_completion" ||
                v.status === "outcome_unknown" ||
                v.status === "verification_failed"
                  ? "Reconcile and retry approved updates"
                  : "Execute approved ERP and Planner updates"}
              </button>
            </AllowedAction>
          </>
        )}
      </Section>
      <Section
        title="Actions taken and confirmed"
        note="See each saved change and whether a fresh source check confirmed it."
      >
        {v.status === "partial_completion" && (
          <p role="alert">
            Partial completion — ERP update verified; Planner update incomplete.
            Reconciliation required.
          </p>
        )}
        <StatusText tone={v.status === "verified" ? "good" : "neutral"}>
          {words(v.status)}
        </StatusText>
        {p &&
          Object.values(p.steps || {}).map((s) => (
            <article className="cp-record" key={s.operation}>
              <strong>
                {workflowStep(s.operation)} · {traceStatus(s.status)}
              </strong>
              <p>{s.source_id || "No source record verified"}</p>
              {s.error_code && <p>{words(s.error_code)}</p>}
            </article>
          ))}
        {p &&
          !p.decision &&
          ["failed", "outcome_unknown", "verification_failed"].includes(
            v.status,
          ) && (
            <AllowedAction caseId="DR-009" action="reconcile">
              <button
                disabled={
                  busy || !canAct(host.capabilities, "DR-009", "reconcile")
                }
                onClick={() =>
                  void action("/delivery-commitment/reconcile", {
                    run_id: p.run_id,
                  })
                }
              >
                Reconcile proposal preparation
              </button>
            </AllowedAction>
          )}
      </Section>
      <Section
        title="Current business state"
        note="Commercial commitment is separate from customer agreement, technical acceptance and delivery."
      >
        <Facts
          rows={[
            [
              "Authorized release commitment",
              c?.commitment
                ? `${c.commitment.quantity} units · ${date(c.commitment.committed_at, true)} ${c.commitment.date_semantics}`
                : "No revised delivery-release commitment recorded",
            ],
            [
              "Remaining uncommitted",
              `${c?.commitment?.remaining_uncommitted_quantity ?? c?.request.quantity ?? "Unknown"} units`,
            ],
            [
              "Customer agreement",
              c?.commitment?.customer_agreement ||
                c?.request.customer_agreement ||
                "Unknown",
            ],
            [
              "Customer technical acceptance",
              c?.request.technical_change_id
                ? String(
                    (c.technical_dependency?.physical &&
                      (
                        c.technical_dependency.physical as Record<
                          string,
                          unknown
                        >
                      ).customer_acceptance) ||
                      "Unknown",
                  )
                : c?.clearance?.customer_technical_acceptance || "Unknown",
            ],
            [
              "Delivered",
              `${c?.commitment?.delivered_quantity ?? 0} · No shipment recorded`,
            ],
          ]}
        />
        <div className="cp-inline">
          {[
            "erp",
            "programs",
            "manufacturing",
            "engineering",
            "validation",
          ].map((system) => (
            <Link key={system} to={`/${system}/delivery/DR-009`}>
              {system === "programs" ? "Planner" : words(system)} source{" "}
              <ArrowRight size={14} />
            </Link>
          ))}
        </div>
        {v.records?.commitments.map((x) => (
          <p key={x.id}>
            {x.id} · {x.quantity} units · {x.status}
          </p>
        ))}
        {v.records?.links.map((x) => (
          <p key={x.id}>
            {x.id} · {x.milestone_id} · {words(x.status)}
          </p>
        ))}
      </Section>
      {(v.runs || []).length > 1 && (
        <details className="cp-secondary-content">
          <summary>Earlier investigations ({v.runs!.length - 1})</summary>
          {v.runs!.slice(1).map((run) => (
            <p key={run.run_id}>
              <Link to={`/control/runs/${run.run_id}`}>
                {words(run.status)} · {date(run.started_at, true)}
              </Link>
            </p>
          ))}
        </details>
      )}
      <KnowledgeRunEvidence caseId="DR-009" />
    </div>
  );
}
