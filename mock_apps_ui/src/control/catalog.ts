// Generated definitions mirror the host registry; runtime reads take precedence.
import definitions from "./workflow-catalog.json" with { type: "json" };
import type { HostSchema } from "./host";
export const catalog = definitions as HostSchema["CatalogWorkflow"][];

import {
  LayoutDashboard,
  Layers,
  Workflow,
  ClipboardCheck,
  GitFork,
  BookOpen,
  Activity,
} from "lucide-react";

export const navigation = [
  ["Overview", "/control/overview", LayoutDashboard],
  ["Programs", "/control/programs", Layers],
  ["Workflows & Automations", "/control/workflows", Workflow],
  ["Decisions", "/control/decisions", ClipboardCheck],
  ["Scenarios", "/control/scenarios", GitFork],
  ["Knowledge & Evidence", "/control/knowledge", BookOpen],
  ["Operations", "/control/operations", Activity],
] as const;
