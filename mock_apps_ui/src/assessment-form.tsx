import { Link, useNavigate } from "react-router-dom";
import { enc, type Schema } from "./api";
import { useData, useFormState, type Case } from "./data";
import { useMutation } from "./mutations";
import { OptionSummary } from "./engineering";
import { ScheduledWork } from "./case-progress";
import { FieldValue, SourceReference, sourceKey } from "./sources";
import {
  Banner,
  date,
  Empty,
  Facts,
  Heading,
  human,
  money,
  Panel,
  Table,
} from "./ui";

type FactForm = { text: string; sources: string[] };
type Form = {
  selection: string;
  facts: FactForm[];
  gaps: string[];
  questions: string[];
};

function AssessmentSummary({
  assessment,
}: {
  assessment: Schema["PlanView"]["assessment"];
}) {
  return (
    <div className="assessment-summary">
      {assessment.facts.map((fact, i) => (
        <div key={i}>
          <p>
            <strong>Fact {i + 1}.</strong> {fact.text}
          </p>
          <small>
            Sources: {fact.source_refs.map((s) => s.resource_id).join(", ")}
          </small>
        </div>
      ))}
      {!!assessment.evidence_gaps.length && (
        <>
          <strong>Evidence gaps</strong>
          <ul>
            {assessment.evidence_gaps.map((gap, i) => (
              <li key={i}>{gap}</li>
            ))}
          </ul>
        </>
      )}
      {!!assessment.unresolved_questions.length && (
        <>
          <strong>Open questions</strong>
          <ul>
            {assessment.unresolved_questions.map((question, i) => (
              <li key={i}>{question}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

export function ScopeChanges({
  previous,
  current,
}: {
  previous: Schema["PlanView"];
  current: Schema["PlanView"];
}) {
  const fields = [
    "target_requirement_revision_id",
    "configuration_id",
    "procedure_id",
    "sample_id",
    "slot_id",
    "milestone_id",
    "policy_id",
    "cost_cents",
    "review_minutes",
    "permitted_actions",
    "timing",
    "assessment",
  ] as const;
  const changed = fields.filter(
    (key) => JSON.stringify(previous[key]) !== JSON.stringify(current[key]),
  );
  const sources = current.source_snapshot.filter((s) => {
    const old = previous.source_snapshot.find(
      (p) => sourceKey(p) === sourceKey(s),
    );
    return (
      !old ||
      old.content_digest !== s.content_digest ||
      old.content_version !== s.content_version ||
      old.availability_version !== s.availability_version
    );
  });
  const removed = previous.source_snapshot.filter(
    (s) => !current.source_snapshot.some((r) => sourceKey(r) === sourceKey(s)),
  );
  return (
    <Panel title="Changes from the preceding plan">
      <p className="padded">
        Revises{" "}
        <Link className="record-link" to={"/engineering/plans/" + previous.id}>
          {previous.id}
        </Link>
        . Each plan has its own immutable version and requires its own decision.
      </p>
      {changed.length ? (
        <Table headers={["Changed field", "Earlier plan", "This plan"]}>
          {changed.map((key) => (
            <tr key={key}>
              <td>{key === "cost_cents" ? "Incremental cost" : human(key)}</td>
              <td>
                {key === "assessment" ? (
                  <AssessmentSummary assessment={previous.assessment} />
                ) : (
                  <FieldValue name={key} value={previous[key]} />
                )}
              </td>
              <td className="changed-value">
                {key === "assessment" ? (
                  <AssessmentSummary assessment={current.assessment} />
                ) : (
                  <FieldValue name={key} value={current[key]} />
                )}
              </td>
            </tr>
          ))}
        </Table>
      ) : (
        <Empty>
          No selected scope or assessment fields changed. This is still a
          separate plan requiring fresh approval.
        </Empty>
      )}
      <details className="padded">
        <summary>
          Source changes · {sources.length} added or changed · {removed.length}{" "}
          removed
        </summary>
        {sources.map((s) => (
          <div key={sourceKey(s)}>
            <SourceReference source={s} snapshot={s} />
          </div>
        ))}
        {removed.map((s) => (
          <p key={sourceKey(s)}>Removed: {s.resource_id}</p>
        ))}
        {!sources.length && !removed.length && (
          <p>No critical source or availability versions changed.</p>
        )}
      </details>
    </Panel>
  );
}

export function DraftPlan({
  c,
  previous,
}: {
  c: Case;
  previous?: Schema["PlanView"];
}) {
  const { persona, error: sourceError, loading } = useData();
  const navigate = useNavigate();
  const initial: Form = {
    selection: "",
    facts: previous
      ? previous.assessment.facts.map((f) => ({
          text: f.text,
          sources: f.source_refs.map(sourceKey),
        }))
      : [{ text: "", sources: [""] }],
    gaps: previous?.assessment.evidence_gaps.length
      ? previous.assessment.evidence_gaps
      : [""],
    questions: previous?.assessment.unresolved_questions.length
      ? previous.assessment.unresolved_questions
      : [""],
  };
  const intent =
    "draft:" + c.change.id + (previous ? ":revision:" + previous.id : "");
  // Preserve unfinished forms from the earlier single-fact UI and its retry key.
  const [saved, setForm] = useFormState<
    Form & { fact?: string; source?: string; gap?: string; question?: string }
  >(intent, initial);
  const form: Form = saved.facts
    ? saved
    : {
        selection: saved.selection,
        facts: [{ text: saved.fact || "", sources: [saved.source || ""] }],
        gaps: [saved.gap || ""],
        questions: [saved.question || ""],
      };
  const mutation = useMutation(intent, (record) => {
    setForm(initial);
    navigate("/engineering/plans/" + record.id);
  });
  const selected = c.options.find(
    (o) => o.slot.id + "|" + o.sample.id === form.selection,
  );
  const availableSources = selected?.expected_source_versions.records || [];
  const validFacts =
    form.facts.length > 0 &&
    form.facts.every(
      (f) =>
        f.text.trim() &&
        f.sources.length > 0 &&
        f.sources.every((key) =>
          availableSources.some((s) => sourceKey(s) === key),
        ) &&
        new Set(f.sources).size === f.sources.length,
    );
  const updateFact = (index: number, value: FactForm) =>
    setForm({
      ...form,
      facts: form.facts.map((f, i) => (i === index ? value : f)),
    });
  const closed = ["closed", "superseded"].includes(c.change.workflow_state);
  const disabled =
    closed ||
    persona !== "automation" ||
    !!sourceError ||
    loading ||
    mutation.busy ||
    mutation.pending;
  const canDraft = c.options.some((o) => o.resource_eligible);
  return (
    <>
      <Heading
        eyebrow={"Engineering / " + c.change.id}
        title={
          previous
            ? "Create revised plan"
            : "Draft assessment & validation plan"
        }
      >
        Record sourced facts, evidence gaps and open questions. Timing and cost
        are calculated before the plan is frozen.
      </Heading>
      {previous && (
        <Banner>
          <strong>
            Revision of{" "}
            <Link
              className="record-link"
              to={"/engineering/plans/" + previous.id}
            >
              {previous.id}
            </Link>
          </strong>
          <p>
            Your assessment is copied for editing. Choose and review the
            resources again. The earlier plan, its decision and any booked work
            remain intact. This revision requires fresh engineering approval.
          </p>
          <p>
            Previous selection: {previous.sample_id} / {previous.slot_id} ·{" "}
            {money(previous.cost_cents)} · review ready{" "}
            {date(previous.timing.review_ready_at)}.
          </p>
        </Banner>
      )}
      {!canDraft && (
        <>
          <ScheduledWork c={c} />
          <Banner tone="warning">
            No eligible resources are available for a new plan. Review{" "}
            <Link to="/validation/options">Validation options</Link>. Existing
            work cannot be cancelled or released here.
          </Banner>
        </>
      )}
      {persona !== "automation" && (
        <Banner>
          Select Program operator to create a draft. Engineering approvers
          cannot author it.
        </Banner>
      )}
      {closed && (
        <Banner tone="warning">
          This change is closed or superseded. Use the active replacement scope
          before drafting.
        </Banner>
      )}
      {mutation.feedback}
      <div className="split wide-left">
        <Panel title="Assessment form">
          <form
            className="form"
            onSubmit={(e) => {
              e.preventDefault();
              if (!selected?.resource_eligible || !validFacts) return;
              const body: Schema["PlanInput"] = {
                expected_change_content_version: c.change.content_version,
                target_requirement_revision_id: c.target.id,
                configuration_id: selected.configuration_id,
                procedure_id: selected.procedure_id,
                sample_id: selected.sample.id,
                slot_id: selected.slot.id,
                milestone_id: selected.milestone_id,
                ...(previous ? { supersedes_plan_id: previous.id } : {}),
                assessment: {
                  facts: form.facts.map((f) => ({
                    text: f.text,
                    source_refs: f.sources.map((key) => {
                      const source = availableSources.find(
                        (s) => sourceKey(s) === key,
                      )!;
                      return {
                        resource_type: source.resource_type,
                        resource_id: source.resource_id,
                      };
                    }),
                  })),
                  evidence_gaps: form.gaps.filter((s) => s.trim()),
                  unresolved_questions: form.questions.filter((s) => s.trim()),
                },
                expected_source_versions: selected.expected_source_versions,
              };
              void mutation.submit(
                `/engineering/changes/${enc(c.change.id)}/plans`,
                body,
              );
            }}
          >
            <fieldset disabled={disabled}>
              <label>
                Validation option
                <select
                  required
                  aria-label="Validation option"
                  value={form.selection}
                  onChange={(e) =>
                    setForm({ ...form, selection: e.target.value })
                  }
                >
                  <option value="">Choose a slot and sample</option>
                  {c.options.map((o) => (
                    <option
                      key={o.slot.id + o.sample.id}
                      value={o.slot.id + "|" + o.sample.id}
                      disabled={!o.resource_eligible}
                    >
                      {o.slot.id} / {o.sample.id} · {money(o.cost_cents)} ·{" "}
                      {o.resource_eligible
                        ? o.meets_deadline
                          ? "before deadline"
                          : "after deadline"
                        : "ineligible (see Validation options)"}
                    </option>
                  ))}
                </select>
              </label>
              <div className="form-section-title">
                <h3>Sourced facts</h3>
                <span>{form.facts.length} / 30</span>
              </div>
              {form.facts.map((fact, index) => (
                <div className="fact-editor" key={index}>
                  <div className="form-section-title">
                    <strong>Fact {index + 1}</strong>
                    {form.facts.length > 1 && (
                      <button
                        type="button"
                        onClick={() =>
                          setForm({
                            ...form,
                            facts: form.facts.filter((_, i) => i !== index),
                          })
                        }
                      >
                        Remove fact {index + 1}
                      </button>
                    )}
                  </div>
                  <label>
                    {index === 0
                      ? "Assessment fact"
                      : "Assessment fact " + (index + 1)}
                    <textarea
                      required
                      maxLength={2000}
                      value={fact.text}
                      onChange={(e) =>
                        updateFact(index, { ...fact, text: e.target.value })
                      }
                      placeholder="Describe an established fact from the selected sources."
                    />
                  </label>
                  {fact.sources.map((key, sourceIndex) => {
                    const source = availableSources.find(
                      (s) => sourceKey(s) === key,
                    );
                    return (
                      <div className="citation-editor" key={sourceIndex}>
                        <label>
                          {index === 0 && sourceIndex === 0
                            ? "Supporting source"
                            : `Supporting source ${index + 1}.${sourceIndex + 1}`}
                          <select
                            required
                            aria-label={
                              index === 0 && sourceIndex === 0
                                ? "Supporting source"
                                : `Supporting source ${index + 1}.${sourceIndex + 1}`
                            }
                            value={key}
                            onChange={(e) =>
                              updateFact(index, {
                                ...fact,
                                sources: fact.sources.map((s, i) =>
                                  i === sourceIndex ? e.target.value : s,
                                ),
                              })
                            }
                          >
                            <option value="">Choose a retrieved source</option>
                            {key && !source && (
                              <option value={key} disabled>
                                {key.split("|")[1]} · reselect from current
                                option
                              </option>
                            )}
                            {availableSources.map((s) => (
                              <option
                                key={sourceKey(s)}
                                value={sourceKey(s)}
                                disabled={
                                  fact.sources.includes(sourceKey(s)) &&
                                  key !== sourceKey(s)
                                }
                              >
                                {s.resource_id} ·{" "}
                                {human(s.resource_type.split(".")[1])} · content
                                v{s.content_version}
                              </option>
                            ))}
                          </select>
                        </label>
                        {source && (
                          <SourceReference
                            source={source}
                            expectedVersion={source.content_version}
                          />
                        )}
                        {fact.sources.length > 1 && (
                          <button
                            type="button"
                            onClick={() =>
                              updateFact(index, {
                                ...fact,
                                sources: fact.sources.filter(
                                  (_, i) => i !== sourceIndex,
                                ),
                              })
                            }
                          >
                            Remove citation {index + 1}.{sourceIndex + 1}
                          </button>
                        )}
                      </div>
                    );
                  })}
                  <button
                    type="button"
                    disabled={!selected || fact.sources.length >= 20}
                    onClick={() =>
                      updateFact(index, {
                        ...fact,
                        sources: [...fact.sources, ""],
                      })
                    }
                  >
                    Add citation to fact {index + 1}
                  </button>
                </div>
              ))}
              <button
                type="button"
                disabled={form.facts.length >= 30}
                onClick={() =>
                  setForm({
                    ...form,
                    facts: [...form.facts, { text: "", sources: [""] }],
                  })
                }
              >
                Add fact
              </button>
              {(
                [
                  ["gaps", "Evidence gap"],
                  ["questions", "Unresolved question"],
                ] as const
              ).map(([key, label]) => (
                <div className="assessment-list" key={key}>
                  {form[key].map((text, index) => (
                    <div key={index}>
                      <label>
                        {label + (index ? " " + (index + 1) : "")}
                        <textarea
                          maxLength={2000}
                          value={text}
                          onChange={(e) =>
                            setForm({
                              ...form,
                              [key]: form[key].map((t, i) =>
                                i === index ? e.target.value : t,
                              ),
                            })
                          }
                        />
                      </label>
                      {form[key].length > 1 && (
                        <button
                          type="button"
                          onClick={() =>
                            setForm({
                              ...form,
                              [key]: form[key].filter((_, i) => i !== index),
                            })
                          }
                        >
                          Remove {label.toLowerCase()} {index + 1}
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    type="button"
                    disabled={form[key].length >= 30}
                    onClick={() =>
                      setForm({ ...form, [key]: [...form[key], ""] })
                    }
                  >
                    Add {label.toLowerCase()}
                  </button>
                </div>
              ))}
              <button
                className="primary"
                type="submit"
                disabled={!selected?.resource_eligible || !validFacts}
              >
                Create immutable {previous ? "revision" : "draft"}
              </button>
            </fieldset>
          </form>
        </Panel>
        <div>
          <Panel title="Selected option">
            {selected ? (
              <OptionSummary option={selected} />
            ) : (
              <Empty>
                No option selected. Compare all options in{" "}
                <Link to="/validation/options">Stratos TestOps</Link>.
              </Empty>
            )}
          </Panel>
          <Panel title="Scope of this request">
            <Facts
              items={[
                ["Requested requirement", c.target.id],
                ["Configuration", c.config.id],
                ["Milestone", c.milestone.name],
                ["Baseline deadline", date(c.milestone.baseline_at)],
                [
                  "Evidence coverage",
                  c.coverage.coverage_satisfied ? "Satisfied" : "Incomplete",
                ],
              ]}
            />
          </Panel>
          {previous && selected && (
            <Panel title="Review revised resource selection">
              <Facts
                items={[
                  ["Earlier slot", previous.slot_id],
                  ["New slot", selected.slot.id],
                  ["Earlier sample", previous.sample_id],
                  ["New sample", selected.sample.id],
                  [
                    "Cost change",
                    money(selected.cost_cents - previous.cost_cents),
                  ],
                ]}
              />
              <p className="padded">
                The saved revision will show all changed scope, assessment and
                source fields before a new decision is recorded.
              </p>
            </Panel>
          )}
        </div>
      </div>
    </>
  );
}
