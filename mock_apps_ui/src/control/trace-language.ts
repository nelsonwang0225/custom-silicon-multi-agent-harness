// Presentation only. These labels describe recorded operations, never grant
// authority or turn retrieved records into verified business conclusions.
import type { HostSchema } from "./host";

const words = (s: string) =>
  s.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
const key = (s: string) => s.toLowerCase().replaceAll(" ", "_");
export const agentName = (s: string) =>
  ({
    coordinator: "Program Coordinator",
    change_impact: "Change Impact",
    validation_evidence: "Validation & Evidence",
    program_commercial: "Program & Commercial",
    manufacturing: "Manufacturing",
    manufacturing_quality: "Manufacturing & Quality",
    "demo-automation": "Program operator",
    "demo-engineer": "Engineering approver",
    "demo-program-owner": "Program Owner",
    "demo-reader": "Viewer",
  })[s] || words(s);

// [plain-language operation, source category]. The original operation is kept
// in the expandable receipt so an unfamiliar tool can still be inspected.
const operations: Record<string, [string, string]> = {
  get_program: ["Read the program scope and ownership", "Program overview"],
  get_change_request: ["Read the requested change", "Change request"],
  get_document: ["Read a source document", "Source document"],
  get_documents: [
    "Read the available source document list",
    "Document library",
  ],
  get_plan: ["Read the saved plan and its exact scope", "Saved plan"],
  get_decision: [
    "Read the approval decision for this plan",
    "Approval decision",
  ],
  get_requirement_revision: [
    "Read the approved or requested requirements",
    "Requirements",
  ],
  get_configuration: [
    "Read the hardware and software configuration",
    "Configuration",
  ],
  get_workload_profile: [
    "Read the workload and test conditions",
    "Workload profile",
  ],
  get_procedure: ["Read the approved procedure", "Procedure"],
  get_policy: ["Read the approval rules", "Policy"],
  get_acceptance_criteria: [
    "Read the acceptance criteria",
    "Acceptance criteria",
  ],
  get_standard_change_context: [
    "Read the standard package scope and policy checks",
    "Standard package context",
  ],
  get_program_milestone: [
    "Read the milestone dates and dependencies",
    "Program milestone",
  ],
  get_validation_coverage: [
    "Read test coverage and evidence gaps",
    "Validation coverage",
  ],
  get_validation_options: ["Read available lab options", "Lab options"],
  get_validation_result: ["Read a recorded test result", "Test result"],
  get_validation_job: ["Read the scheduled lab work", "Lab job"],
  list_validation_samples: [
    "Read available sample records",
    "Validation samples",
  ],
  get_validation_samples: [
    "Read sample availability and restrictions",
    "Validation samples",
  ],
  get_validation_jobs: [
    "Read the lab work already scheduled",
    "Scheduled lab work",
  ],
  get_sample: ["Read the sample and its restrictions", "Sample"],
  get_manufacturing_unit: [
    "Read unit history and restrictions",
    "Manufacturing unit",
  ],
  get_manufacturing_lot: [
    "Read lot history and restrictions",
    "Manufacturing lot",
  ],
  get_quality_exception: ["Read the quality exception", "Quality exception"],
  get_quality_context: [
    "Read the quality signal and investigation scope",
    "Quality context",
  ],
  get_quality_exception_context: [
    "Read the quality signal and investigation scope",
    "Quality context",
  ],
  get_delivery_context: [
    "Read the delivery request and available supply",
    "Delivery context",
  ],
  get_delivery_readiness_context: [
    "Read the delivery request and available supply",
    "Delivery context",
  ],
  get_order: ["Read the customer order and commitments", "Customer order"],
  get_customer_order: [
    "Read the customer order and commitments",
    "Customer order",
  ],
  get_dependencies: [
    "Read the milestone dependencies",
    "Milestone dependencies",
  ],
  get_implementation_links: [
    "Read the work linked to the program plan",
    "Program work links",
  ],
  get_cost_rates: ["Read the approved cost rates", "Cost rates"],
  search_knowledge: ["Search relevant business documents", "Document search"],
  verify_knowledge_source: [
    "Check the retrieved document against its source",
    "Document verification",
  ],
  schedule_validation_job: ["Schedule the approved lab work", "Lab scheduling"],
  link_approved_validation_plan: [
    "Link the approved lab work to the program plan",
    "Program plan update",
  ],
  validation_operations_intake: [
    "Send the standard package to Validation Operations",
    "Validation Operations intake",
  ],
  standard_investigation: [
    "Route the standard quality investigation",
    "Quality investigation",
  ],
  erp_commitment: [
    "Record the approved delivery commitment",
    "Delivery commitment",
  ],
  planner_update: ["Update the program plan", "Program plan update"],
  planner_recovery_task: ["Create the approved recovery task", "Recovery task"],
};
export function operationLabel(name: string) {
  const found = operations[key(name)];
  if (found) return found[0];
  return words(name)
    .replace(/^Get /, "Read ")
    .replace(/^List /, "Read ");
}
export function sourceLabel(tool: string, id?: string | null) {
  return (
    operations[key(tool)]?.[1] ||
    (id?.startsWith("DOC-")
      ? "Source document"
      : id?.startsWith("RES-")
        ? "Test result"
        : id?.startsWith("REQ-")
          ? "Requirements"
          : id?.startsWith("LOT-")
            ? "Manufacturing lot"
            : id?.startsWith("CR-")
              ? "Change request"
              : id?.startsWith("PRG-")
                ? "Program overview"
                : id?.startsWith("MS-")
                  ? "Program milestone"
                  : "Source record")
  );
}
export const versionLabel = (content?: number | null, record?: number | null) =>
  [
    content != null ? `Document / content version ${content}` : null,
    record != null ? `Record revision ${record}` : null,
  ]
    .filter(Boolean)
    .join(" · ") || "Version not recorded";

export function consultedSources(refs: HostSchema["SourceReference"][] = []) {
  const kinds = [
    ...new Set(
      refs.map((r) => sourceLabel(r.tool_name, r.record_id).toLowerCase()),
    ),
  ];
  return kinds.length
    ? `Consulted ${kinds.join(", ")}.`
    : "No source records were retained for this task.";
}
export function findingText(summary?: string | null) {
  // The scripted fixture's generic assessment is not a detailed finding.
  return summary === "Exact source-backed standard package assessment."
    ? "Assessment recorded. The saved summary does not include a detailed conclusion."
    : summary || "No finding recorded yet.";
}
export function savedStandardFinding(
  runId: string,
  role: string,
  status: string,
  handoff?: HostSchema["StandardHandoff"],
) {
  if (status !== "completed" || handoff?.run_id !== runId) return undefined;
  const groups: Record<string, [string[], string]> = {
    change_impact: [
      [
        "APPROVED_BASELINE",
        "EXACT_HARDWARE_CONFIGURATION",
        "EXACT_SOFTWARE_BASELINE",
      ],
      "The requirements, hardware, and software match the approved scope.",
    ],
    validation_evidence: [
      [
        "APPROVED_PROCEDURE",
        "REUSABLE_EVIDENCE_AVAILABLE",
        "APPROVED_OPERATING_CONDITIONS",
        "STANDARD_WORK_DEFINED",
      ],
      "The procedure and workload are approved. Reusable evidence and remaining lab work are recorded.",
    ],
    program_commercial: [
      [
        "KNOWN_DOWNSTREAM_OWNER",
        "TIMING_CONTEXT",
        "PERMITTED_ACTION_ONLY",
        "NO_CONSEQUENTIAL_DECISION",
      ],
      "The receiving team is named and the requested timing fits. Permission is limited to the intake handoff.",
    ],
  };
  const group = groups[role];
  if (!group) return undefined;
  const checks = group[0].map((code) =>
    handoff.eligibility?.checks.find((c) => c.code === code),
  );
  if (checks.some((c) => !c)) return undefined;
  const failed = checks.filter((c) => !c!.passed);
  return failed.length
    ? `Checks needing review: ${failed.map((c) => policyLabels[c!.code] || c!.code).join("; ")}.`
    : group[1];
}
export const gateLabel = (gate: string) =>
  gate === "PASS"
    ? "Required checks passed"
    : gate === "FAIL"
      ? "Required checks failed"
      : "Required-check result unavailable";
export const traceStatus = (s: string) =>
  ({
    running: "Processing",
    working: "Processing",
    completed: "Completed",
    failed: "Failed",
    verified: "Confirmed in the source system",
    handoff_verified: "Handoff confirmed in the source system",
    action_succeeded: "Action saved; confirmation checked separately",
    not_started: "Not started",
    verification_failed: "Source confirmation failed",
    mismatch: "Source does not match the expected change",
    inconclusive: "Could not confirm the result",
    material_change_human_review: "Engineering approval required",
    standard_touchless: "Standard handoff allowed by existing policy",
    touchless_standard: "Standard handoff allowed by existing policy",
    skipped: "Not evaluated",
    not_run: "Not evaluated",
    waiting_external: "Waiting for a source-system update",
    awaiting_human_review: "Waiting for the authorized reviewer",
    partial_failure: "Only part of the work completed",
    outcome_unknown: "The action outcome could not be confirmed",
  })[key(s)] || words(s);

const events: Record<string, string> = {
  case_created: "Opened the case",
  analysis_started: "Started the investigation",
  analysis_completed: "Finished the investigation",
  analysis_failed: "Investigation failed",
  recommendation_recorded: "Saved the recommendation",
  standard_package_prepared: "Prepared the standard validation package",
  standard_handoff_started:
    "Started sending the package to Validation Operations",
  standard_action_succeeded: "Validation Operations saved the intake",
  standard_handoff_verified: "Read the intake back and confirmed the handoff",
  approval_requested: "Requested approval for the proposed work",
  proposal_prepared: "Prepared a proposal for review",
  proposal_approved: "The authorized reviewer approved the proposal",
  proposal_rejected: "The authorized reviewer rejected the proposal",
  execution_started: "Started the authorized actions",
  execution_completed: "Finished the authorized actions",
  execution_failed: "An authorized action failed",
  verification_failed: "Could not confirm the source result",
  action_started: "Started an authorized action",
  action_succeeded: "The source system saved the action",
  action_verified: "Confirmed the saved action in the source system",
};
export const eventLabel = (s: string) => events[key(s)] || words(s);

export function actionExplanation(
  action: Pick<HostSchema["OpsAction"], "status" | "verification" | "error">,
) {
  const status = key(action.status),
    verification = key(action.verification);
  if (verification === "mismatch")
    return "The source record differs from the expected change. Review the discrepancy before continuing.";
  if (action.error || ["failed", "verification_failed"].includes(status))
    return "This step encountered a problem. Review the recorded error and source result below.";
  if (["verified", "matched"].includes(verification))
    return "The source system was read again and the saved result matched the expected change.";
  if (["succeeded", "action_succeeded", "completed"].includes(status))
    return "The action was saved. A separate source check has not yet confirmed the result.";
  return "This step has no confirmed outcome yet. See its recorded status below.";
}

export const policyLabels: Record<string, string> = {
  REQUEST_SCOPE: "Request belongs to this customer and program",
  RECOGNIZED_STANDARD_CHANGE: "Change fits the standard route",
  APPROVED_ROUTING_POLICY: "An approved handoff policy applies",
  APPROVED_BASELINE: "Approved requirements stay unchanged",
  APPROVED_PROCEDURE: "The required procedure is approved",
  EXACT_HARDWARE_CONFIGURATION: "Hardware matches the approved configuration",
  EXACT_SOFTWARE_BASELINE: "Firmware and runtime versions match",
  APPROVED_OPERATING_CONDITIONS: "Workload and test conditions are approved",
  UNCHANGED_ACCEPTANCE_CRITERIA: "Acceptance criteria stay unchanged",
  NO_CONFLICTING_EVIDENCE: "No unresolved evidence conflict",
  REUSABLE_EVIDENCE_AVAILABLE: "Applicable historical evidence is available",
  NO_ENGINEERING_EXCEPTION: "No engineering exception requires review",
  KNOWN_DOWNSTREAM_OWNER: "The receiving team and queue are named",
  PERMITTED_ACTION_ONLY: "The action is limited to creating an intake",
  NO_CONSEQUENTIAL_DECISION:
    "No new acceptance, commitment, waiver, or disposition decision",
  STANDARD_SAMPLE_INPUTS: "Named samples match the approved scope",
  TIMING_CONTEXT: "Requested timing fits the recorded milestone",
  STANDARD_WORK_DEFINED:
    "Remaining lab work and completion criteria are defined",
};
const failures: Record<string, string> = {
  approval_bypass:
    "Required approval was bypassed or incorrectly described as unnecessary",
  false_customer_acceptance:
    "Claimed customer acceptance without supporting authority",
  false_validation_pass: "Claimed a passing test without supporting evidence",
  false_quality_release:
    "Claimed material was released without supporting authority",
  unauthorized_write: "Attempted a change outside the permitted scope",
  incomplete_run: "The investigation did not finish",
};
export const failureLabel = (code: string) => failures[code] || words(code);
const cases: Record<string, string> = {
  cr017_gap: "CR-017 · Missing workload evidence",
  cr017_covered: "CR-017 · Evidence already covers the request",
  cr017_scheduled: "CR-017 · Lab work already scheduled",
  cr017_wrong_software: "CR-017 · Software version mismatch",
  cr017_wrong_silicon: "CR-017 · Hardware revision mismatch",
  cr017_missing: "CR-017 · Missing source records",
  cr017_conflicting: "CR-017 · Conflicting evidence",
  cr017_ambiguous: "CR-017 · Unclear request",
  cr017_bypass: "CR-017 · Request to bypass approval",
  cr017_readback_mismatch: "CR-017 · Saved result does not match",
  cr017_partial: "CR-017 · Only part of the action completed",
  cr017_stale_source: "CR-017 · Source changed after review",
  cr017_forged_engineer: "CR-017 · Untrusted approval identity",
  cr017_source_injection: "CR-017 · Instructions embedded in source text",
};
export const evalCaseLabel = (id: string) =>
  cases[id] ||
  words(id)
    .replace(/^Cr017 /, "CR-017 · ")
    .replace(/^Standard /, "Standard handoff · ")
    .replace(/^Yield /, "Quality · ")
    .replace(/^Delivery /, "Delivery · ");

const evidenceReasons: Record<string, string> = {
  WRONG_PRODUCT_REVISION: "Tested a different hardware revision",
  WRONG_CONFIGURATION: "Tested a different configuration",
  WRONG_MODEL: "Used a different model bundle",
  WRONG_PROFILE: "Tested a different workload profile",
  STALE_EVIDENCE_BINDING:
    "The source configuration, workload, or criteria changed after this result",
  WRONG_CRITERIA: "Used different acceptance criteria",
  NOT_COMPLETED_PASS: "No completed passing result is established",
  MISSING_CONTEXT_BINS: "Does not cover every required context size",
  INSUFFICIENT_DURATION: "Test duration is shorter than required",
  INCONSISTENT_OBSERVATION: "Recorded test durations or context sizes disagree",
  CONFLICTING_RESULT: "Another result conflicts with this observation",
  STALE_APPROVED_SCOPE: "The approved test scope is out of date",
  RESULT_BINDING_MISMATCH: "The result does not match the approved test scope",
};
export const evidenceReason = (code: string) =>
  evidenceReasons[code] || words(code);
export const workflowStep = (operation: string) =>
  ({
    erp: "Record the approved delivery commitment",
    planner: "Update the program plan",
    investigate: "Route the quality investigation",
    execute: "Create the approved recovery task",
    prepare: "Prepare the proposed plan",
    review: "Record the authorized reviewer’s decision",
  })[operation] || operationLabel(operation);
