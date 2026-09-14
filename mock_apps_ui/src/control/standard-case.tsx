import { KnowledgeRunEvidence } from "./knowledge-runs";
import { policyLabels, traceStatus } from "./trace-language";
import { CaseHeader } from "./case-experience";
import { ActionAccess } from "./persona";
import { useRef, useState } from "react";
import { Link, AllowedAction, canAct } from "./access";
import { ArrowRight, Play } from "lucide-react";
import { useHost, type HostSchema } from "./host";
import { RuntimeLabel } from "./runtime-label";
import { date, words } from "./data";
import {
  Crumbs,
  Empty,
  Facts,
  Heading,
  Section,
  SourceLink,
  StatusText,
  Steps,
} from "./ui";
import { RunFindings } from "./connected-case";
import { standardRunHandoff } from "./experience-model";
export const standardCasePath = "/control/programs/PRG-A17/cases/CR-019";
export const standardAttention = (v: HostSchema["StandardCaseView"]) =>
  (!!v.runs.length &&
    [
      "review_required",
      "source_unavailable",
      "write_failed",
      "outcome_unknown",
      "verification_failed",
      "action_succeeded",
    ].includes(standardRunHandoff(v)?.status || "")) ||
  v.runs[0]?.status === "failed";

export function StandardSummary() {
  const host = useHost(),
    v = host?.data?.standard;
  if (!v) return null;
  return (
    <Section
      title="Standard change"
      note="Helios Atlas Inference · CR-019 · Connected"
    >
      <StatusText
        tone={
          standardAttention(v)
            ? "warning"
            : standardRunHandoff(v)?.status === "handoff_verified"
              ? "good"
              : "neutral"
        }
      >
        {standardRunHandoff(v)?.status === "handoff_verified"
          ? "Handoff verified"
          : words(v.status)}
      </StatusText>
      <p>
        Approved-profile package update. Validation Operations owns the
        remaining lab work.
      </p>
      <Link className="cp-text-link" to={standardCasePath}>
        Inspect standard change <ArrowRight size={15} />
      </Link>
    </Section>
  );
}

export function HandoffDetails({
  handoff,
}: {
  handoff: HostSchema["StandardHandoff"];
}) {
  const p = handoff.package,
    i = handoff.intake;
  return (
    <>
      <details className="cp-secondary-content">
        <summary>Handoff package & remaining standard work</summary>
        <Section
          title="Handoff package"
          note={
            p
              ? `${p.package_id} · Version ${p.package_version}`
              : "No package authorized"
          }
        >
          {p ? (
            <>
              <Facts
                rows={[
                  [
                    "Program / request",
                    `${p.program_id} / ${p.change_id} · ${p.customer_request_reference}`,
                  ],
                  [
                    "Approved procedure",
                    `${p.procedure_id} · v${p.procedure_content_version}`,
                  ],
                  [
                    "Configuration",
                    `${p.configuration.configuration_id} · ${p.configuration.product_revision} · ${p.configuration.firmware} · ${p.configuration.runtime}`,
                  ],
                  ["Reusable evidence", p.reusable_evidence_ids.join(", ")],
                  [
                    "Samples / requested timing",
                    `${p.sample_ids.join(", ")} · ${date(p.requested_at, true)}`,
                  ],
                  [
                    "Owner / queue",
                    `${p.downstream_owner} · ${p.downstream_queue_id}`,
                  ],
                  [
                    "Authority",
                    "Bounded pre-authorized handoff · No new human approval",
                  ],
                ]}
              />
              <h3>Remaining standard work</h3>
              {p.remaining_work.map((w) => (
                <article className="cp-record" key={w.work_id}>
                  <strong>
                    {w.work_id} · {w.procedure_step}
                  </strong>
                  <p>{w.description}</p>
                  <p>Inputs: {w.required_inputs.join(" · ")}</p>
                  <small>{w.completion_criteria}</small>
                </article>
              ))}
              <h3>Handoff completion criteria</h3>
              <ul>
                {p.completion_criteria.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
              <details>
                <summary>Exact package and source provenance</summary>
                <pre className="cp-digest">{JSON.stringify(p, null, 2)}</pre>
              </details>
            </>
          ) : (
            <Empty>
              {(handoff.reasons || []).join(" ") ||
                "The current request requires reassessment."}
            </Empty>
          )}
        </Section>
      </details>
      <Section
        title="Source handoff & independent verification"
        note="The receiving system must confirm the recorded intake."
      >
        <Facts
          rows={[
            ["Action status", traceStatus(handoff.action_status)],
            ["Source confirmation", traceStatus(handoff.verification_status)],
            [
              "Intake",
              i ? (
                <SourceLink to={`/validation/intakes/${i.id}`}>
                  {i.id}
                </SourceLink>
              ) : (
                "Not confirmed"
              ),
            ],
            ["Validation Operations", i ? "Received" : "Receipt not confirmed"],
            [
              "Package",
              i
                ? `Complete · ${handoff.verification_status === "verified" ? "Verified" : "Verification pending"}`
                : "Not confirmed",
            ],
            [
              "Replay",
              handoff.reused_existing
                ? "Existing intake reused"
                : "Original handoff",
            ],
          ]}
        />
        {handoff.error_code && (
          <p role="status" className="cp-error">
            {words(handoff.error_code)}
          </p>
        )}
      </Section>
      <Section
        title="Downstream responsibilities"
        note="The connected agent workflow ends at verified handoff."
      >
        <Facts
          rows={[
            ["Owner", p?.downstream_owner || "Not established"],
            ["Lab authorization", "Pending · Separate authority"],
            ["Physical testing", "Not started"],
            ["Engineering result review", "Pending downstream result"],
            ["Customer acceptance", "Pending"],
          ]}
        />
      </Section>
    </>
  );
}

export function StandardCase() {
  const host = useHost(),
    v = host?.data?.standard,
    c = v?.context,
    h = standardRunHandoff(v),
    run = v?.runs[0];
  const [error, setError] = useState("");
  const lock = useRef(false);
  const active =
    !!host?.data &&
    [...host.data.runs, ...(v?.runs || [])].some((r) => r.status === "running");
  const allowed =
    !!host &&
    !!c &&
    v?.source_available &&
    !host.error &&
    !host.busy &&
    !active &&
    canAct(host.capabilities, "CR-019", "investigate");
  const start = async () => {
    if (!host || !allowed || lock.current) return;
    lock.current = true;
    setError("");
    const key = `stratos.standard-invocation.${host.profile}`;
    let id = sessionStorage.getItem(key);
    if (!id) {
      id = `ui_${crypto.randomUUID().replaceAll("-", "")}`;
      sessionStorage.setItem(key, id);
    }
    try {
      await host.act("/cases/CR-019/investigations", {
        invocation_id: id,
        change_id: "CR-019",
      });
      sessionStorage.removeItem(key);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      lock.current = false;
    }
  };
  const recover = async (retry: boolean) => {
    if (!host || !h) return;
    setError("");
    try {
      await host.act(`/standard-handoffs/${retry ? "retry" : "reconcile"}`, {
        run_id: h.run_id,
        expected_version: h.version,
      });
    } catch (e) {
      setError((e as Error).message);
    }
  };
  if (!v)
    return (
      <Empty>
        Standard case unavailable. Connect the control host and its source
        fixture.
      </Empty>
    );
  const verified = h?.status === "handoff_verified";
  return (
    <div className="cp-case-page cp-case-standard">
      <CaseHeader
        id="CR-019"
        title="Standard validation package"
        action={
          <AllowedAction caseId="CR-019" action="investigate">
            <button
              className="cp-primary"
              disabled={!allowed}
              onClick={() => void start()}
            >
              <Play size={15} />
              {run?.status === "running"
                ? "Investigating…"
                : active
                  ? "Another investigation running"
                  : run
                    ? "Run investigation again"
                    : "Run investigation"}
            </button>
          </AllowedAction>
        }
      />
      <ActionAccess
        caseId="CR-019"
        action="investigate"
        ready={!!c && !!v.source_available && !active}
        reason={
          active
            ? run?.status === "running"
              ? "CR-019 investigation running."
              : "Another case is being investigated. Its result does not change this handoff."
            : "Current source records are required."
        }
      />
      <StatusText
        tone={verified ? "good" : standardAttention(v) ? "warning" : "neutral"}
      >
        {verified ? "Handoff verified" : words(v.status)}
      </StatusText>
      <RuntimeLabel caseId="CR-019" run={run} />
      <p className="cp-caption">
        Program operator initiates; approved policy bounds the handoff.
      </p>
      {(error || host?.error) && (
        <p role="alert" className="cp-error">
          {error || host?.error}
        </p>
      )}
      {!v.source_available && (
        <p role="status">
          Current source context is unavailable. Historical handoff records are
          retained.
        </p>
      )}

      {c && (
        <details className="cp-secondary-content">
          <summary>Request & applicability</summary>
          <Section title="Request & applicability">
            <p>{c.request.summary}</p>
            <Facts
              rows={[
                ["Customer request", c.request.request_reference],
                [
                  "Requirement baseline",
                  `${c.request.baseline_requirement_revision_id} · v${c.request.baseline_content_version} · Unchanged`,
                ],
                ["Requested profile", c.request.workload_profile_id],
                ["Procedure", c.request.procedure_id || "Missing"],
                [
                  "Configuration",
                  c.request.configuration
                    ? `${c.request.configuration.configuration_id} · ${c.request.configuration.product_revision} · ${c.request.configuration.firmware} · ${c.request.configuration.runtime}`
                    : "Missing",
                ],
                ["Requested timing", date(c.request.requested_at, true)],
              ]}
            />
            <SourceLink to="/engineering/changes/CR-019">
              Inspect Engineering request
            </SourceLink>
          </Section>
        </details>
      )}
      {run?.status === "completed" && v.eligibility && (
        <Section
          id="touchless-policy"
          title="Why this handoff can proceed automatically"
          note={
            h
              ? "These checks show the current source state. The saved handoff used the source versions recorded with its investigation."
              : "The source records must meet every rule below. The agents must finish their investigation before the package is sent."
          }
        >
          <StatusText
            tone={v.eligibility.touchless_eligible ? "good" : "warning"}
          >
            {v.eligibility.touchless_eligible
              ? "Exact approved scope matches"
              : "Review or clarification required"}
          </StatusText>
          <details open={!v.eligibility.touchless_eligible}>
            <summary>
              {v.eligibility.checks.filter((x) => x.passed).length} of{" "}
              {v.eligibility.checks.length} checks matched · Inspect policy
            </summary>
            <div className="cp-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Rule</th>
                    <th>Result</th>
                    <th>Requirement</th>
                  </tr>
                </thead>
                <tbody>
                  {v.eligibility.checks.map((x) => (
                    <tr key={x.code}>
                      <td>{policyLabels[x.code] || words(x.code)}</td>
                      <td>{x.passed ? "Matched" : "Blocked"}</td>
                      <td>
                        <details className="tr-details">
                          <summary>Why this is required</summary>
                          <p>{x.reason}</p>
                          <small>Rule: {x.code}</small>
                        </details>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
          <p>
            Reusable evidence:{" "}
            {v.eligibility.reusable_evidence_ids.join(", ") ||
              "None established"}
            . Standard confirmation work remains required after separate lab
            authorization.
          </p>
        </Section>
      )}
      {run && (
        <>
          <RunFindings run={run} />
          <p>
            <Link to={`/control/runs/${run.run_id}`}>
              Inspect recorded run and activity <ArrowRight size={15} />
            </Link>
          </p>
        </>
      )}
      {h && <HandoffDetails handoff={h} />}
      {!h && !!v.handoffs.length && (
        <p className="cp-caption">
          The latest investigation has no handoff result yet.{" "}
          <Link to={`/control/runs/${v.handoffs[0].run_id}`}>
            Inspect the previous run’s handoff result
          </Link>
        </p>
      )}
      {h?.package && !verified && (
        <Section
          title="Handoff recovery"
          note="Unknown outcomes require read-only reconciliation before any further action."
        >
          <AllowedAction caseId="CR-019" action="reconcile">
            <button
              disabled={
                !host ||
                !canAct(host.capabilities, "CR-019", "investigate") ||
                !!host.busy ||
                active
              }
              onClick={() => void recover(false)}
            >
              Reconcile handoff
            </button>
          </AllowedAction>
          {h.action_status === "failed" && (
            <AllowedAction caseId="CR-019" action="reconcile">
              <button disabled={!allowed} onClick={() => void recover(true)}>
                Retry failed handoff
              </button>
            </AllowedAction>
          )}
        </Section>
      )}
      <p className="cp-caption">
        This route creates a Validation Operations intake. Lab authorization,
        scheduling, testing and acceptance remain separate.
      </p>
      <KnowledgeRunEvidence caseId="CR-019" />
    </div>
  );
}
