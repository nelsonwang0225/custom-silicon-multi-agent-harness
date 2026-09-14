import {
  Workflow,
  FileDiff,
  FlaskConical,
  CalendarClock,
  Boxes,
} from "lucide-react";
// Display metadata derived from existing Role / build_agent identities and scoped read permissions.
// Capabilities only; no task assignment, runtime record or execution authority is created here.
export const agentRoles = [
  {
    id: "coordinator",
    name: "Program Coordinator",
    short: "Program Coordinator",
    capability: "Scope the question and reconcile findings",
    sources: "Scoped intake and specialist findings",
    responsibility:
      "Triage a scoped request, consult relevant specialists and reconcile supported findings, uncertainties and escalation needs.",
    icon: Workflow,
  },
  {
    id: "change_impact",
    name: "Change Impact Specialist",
    short: "Change impact",
    capability: "Compare requirements and configuration",
    sources: "Engineering changes, requirement revisions and configuration",
    responsibility:
      "Compare the approved baseline with the requested change. Identify affected technical scope without changing acceptance criteria.",
    icon: FileDiff,
  },
  {
    id: "validation_evidence",
    name: "Validation & Evidence Specialist",
    short: "Validation & evidence",
    capability: "Check applicability and evidence gaps",
    sources:
      "Validation observations, coverage, lab options, procedures and criteria",
    responsibility:
      "Check exact evidence applicability and supported lab options. Scheduling does not establish a passing result or acceptance.",
    icon: FlaskConical,
  },
  {
    id: "program_commercial",
    name: "Program / Commercial Impact Specialist",
    short: "Program & commercial",
    capability: "Assess timing and commercial constraints",
    sources:
      "Program Planner milestones and links; ERP orders and approved rates",
    responsibility:
      "Keep baseline dates, internal forecasts and customer commitments separate while assessing schedule and commercial impact.",
    icon: CalendarClock,
  },
  {
    id: "manufacturing",
    name: "Manufacturing Specialist",
    short: "Manufacturing",
    capability: "Inspect material provenance and restrictions",
    sources: "Manufacturing units, lots, samples and restrictions",
    responsibility:
      "Inspect material restrictions and provenance when a concrete dependency requires it. This role cannot release holds or allocate inventory.",
    icon: Boxes,
  },
] as const;
