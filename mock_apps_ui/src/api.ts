import type { components } from "./schema";
let sourceEpoch: string | null = null;
export type Schema = components["schemas"];
export type Persona = "reader" | "automation" | "engineer" | "program_owner";
export const personas: Record<Persona, string> = {
  program_owner: "Program Owner",
  reader: "Read-only viewer",
  automation: "Program operator",
  engineer: "Engineering approver",
};
export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public details: Record<string, unknown> = {},
    public status?: number,
  ) {
    super(message);
  }
}
export async function request<T>(
  path: string,
  persona: Persona,
  body?: unknown,
  key?: string,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch("/api/v1" + path, {
      method: body === undefined ? "GET" : "POST",
      signal: controller.signal,
      headers: {
        ...(sourceEpoch ? { "X-Stratos-Demo-Epoch": sourceEpoch } : {}),
        Authorization:
          persona === "program_owner"
            ? "Bearer demo-program-owner-local-only"
            : `Bearer demo-portfolio-${persona}-local-only`,
        ...(body === undefined
          ? {}
          : { "Content-Type": "application/json", "Idempotency-Key": key! }),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
    sourceEpoch = response.headers.get("X-Stratos-Demo-Epoch") || sourceEpoch;
    const data = await response.json().catch(() => null);
    if (!response.ok)
      throw new ApiError(
        data?.error?.code || "SERVICE_UNAVAILABLE",
        data?.error?.message ||
          "The API is unavailable. No success has been confirmed.",
        data?.error?.details || {},
        response.status,
      );
    if (!data)
      throw new ApiError(
        "INVALID_RESPONSE",
        "The API returned no readable record. Refresh or retry the same request.",
      );
    return data as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      "CONNECTION_INTERRUPTED",
      body === undefined
        ? "Unable to retrieve current records. Check the connection and refresh."
        : "Connection interrupted or timed out. A write may have committed. Retry the same request to recover its record.",
    );
  } finally {
    clearTimeout(timer);
  }
}
export const enc = encodeURIComponent;
export const api = (persona: Persona) => ({
  get: <T>(path: string) => request<T>(path, persona),
  draft: (id: string, body: Schema["PlanInput"], key: string) =>
    request<Schema["PlanView"]>(
      `/engineering/changes/${enc(id)}/plans`,
      persona,
      body,
      key,
    ),
  decide: (id: string, body: Schema["DecisionInput"], key: string) =>
    request<Schema["Decision"]>(
      `/engineering/plans/${enc(id)}/decisions`,
      persona,
      body,
      key,
    ),
  book: (body: Schema["JobInput"], key: string) =>
    request<Schema["JobView"]>("/validation/jobs", persona, body, key),
  link: (id: string, body: Schema["LinkInput"], key: string) =>
    request<Schema["LinkView"]>(
      `/programs/${enc(id)}/implementation-links`,
      persona,
      body,
      key,
    ),
});
export function errorMessage(error: unknown) {
  if (!(error instanceof ApiError))
    return "Unable to complete the operation. Refresh canonical state and retry.";
  const recovery: Record<string, string> = {
    STALE_SOURCE:
      "Refresh sources and create a revised plan for a new review. Existing bookings are preserved.",
    STALE_MILESTONE:
      "Refresh the milestone and submit the missing planner action again. Keep the existing lab job.",
    RESOURCE_CONFLICT:
      "Refresh availability and recover any existing job before considering a revised plan.",
    FORBIDDEN_ROLE:
      "Select the authorized simulated persona explicitly; the application will not switch roles.",
    APPROVAL_REQUIRED:
      "Choose a plan with a matching recorded engineer approval.",
    APPROVAL_POLICY_EXCEEDED:
      "Engineering authority does not cover this plan. Reassessment or escalation is required.",
    IDEMPOTENCY_KEY_REUSED:
      "This retry key already binds different content. Recover the original request first.",
  };
  const reasons = Array.isArray(error.details.reasons)
    ? error.details.reasons.join(", ")
    : "";
  return `${error.code}: ${error.message} ${recovery[error.code] || ""} ${reasons}`.trim();
}
