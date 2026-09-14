import { useRef, useState } from "react";
import {
  ApiError,
  enc,
  errorMessage,
  request,
  type Persona,
  type Schema,
} from "./api";
import { useData } from "./data";
import { Banner } from "./ui";
type Receipt = {
  path: string;
  body: unknown;
  key: string;
  persona: Persona;
  confirmed?: boolean;
};
type RecordResult = { id: string };
async function readBack(
  receipt: Receipt,
  record: RecordResult,
): Promise<RecordResult> {
  const { path, persona } = receipt;
  if (path.endsWith("/plans"))
    return request(`/engineering/plans/${enc(record.id)}`, persona);
  if (path.endsWith("/decisions"))
    return request(`/engineering/decisions/${enc(record.id)}`, persona);
  if (path === "/validation/jobs")
    return request(`/validation/jobs/${enc(record.id)}`, persona);
  const body = receipt.body as Schema["LinkInput"];
  const plan = await request<Schema["PlanView"]>(
    `/engineering/plans/${enc(body.plan_id)}`,
    persona,
  );
  const links = await request<{ items: Schema["LinkView"][] }>(
    path + "?change_id=" + enc(plan.change_id),
    persona,
  );
  const link = links.items.find((l) => l.id === record.id);
  if (!link)
    throw new ApiError(
      "READBACK_PENDING",
      "The planner write may have committed, but read-back has not confirmed it. Retry the original request.",
    );
  await request(
    `/programs/${enc(plan.program_id)}/milestones/${enc(plan.milestone_id)}`,
    persona,
  );
  return link;
}
export function useMutation(
  intent: string,
  onSuccess?: (record: RecordResult) => void,
) {
  const { persona, changed, refresh } = useData();
  const storage = "retry:" + intent;
  const [pending, setPending] = useState<Receipt | null>(() => {
    try {
      return JSON.parse(sessionStorage.getItem(storage) || "null");
    } catch {
      return null;
    }
  });
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [success, setSuccess] = useState(""),
    [revisable, setRevisable] = useState(false);
  const lock = useRef(false);
  const run = async (receipt: Receipt) => {
    if (lock.current) return;
    if (receipt.persona !== persona) {
      setError(
        "This request belongs to a different simulated persona. Select " +
          receipt.persona +
          " explicitly to retry it.",
      );
      return;
    }
    lock.current = true;
    setBusy(true);
    setError("");
    setSuccess("");
    setRevisable(false);
    setPending(receipt);
    sessionStorage.setItem(storage, JSON.stringify(receipt));
    sessionStorage.setItem(storage + ":last", JSON.stringify(receipt));
    // Only a definitive denial of the POST permits a new intent. Any failure
    // after POST success must retain the original request, even a read-back 403.
    let writeConfirmed = !!receipt.confirmed;
    try {
      let result: RecordResult;
      try {
        result = await request<RecordResult>(
          receipt.path,
          persona,
          receipt.body,
          receipt.key,
        );
      } catch (e) {
        if (
          e instanceof ApiError &&
          e.code === "ACTION_ALREADY_RECORDED" &&
          typeof e.details.existing_resource_id === "string"
        )
          result = { id: e.details.existing_resource_id };
        else throw e;
      }
      writeConfirmed = true;
      receipt.confirmed = true;
      sessionStorage.setItem(storage, JSON.stringify(receipt));
      sessionStorage.setItem(storage + ":last", JSON.stringify(receipt));
      result = await readBack(receipt, result);
      if (!(await changed()))
        throw new ApiError(
          "REFRESH_PENDING",
          "Write read-back succeeded, but workspace refresh failed. Retry to recover the same record.",
        );
      sessionStorage.removeItem(storage);
      sessionStorage.removeItem(storage + ":last");
      setPending(null);
      setSuccess("Saved and verified from the API.");
      onSuccess?.(result);
    } catch (e) {
      setError(errorMessage(e));
      setRevisable(
        !writeConfirmed &&
          e instanceof ApiError &&
          e.status !== undefined &&
          e.status >= 400 &&
          e.status < 500 &&
          ![
            "CONNECTION_INTERRUPTED",
            "DATABASE_BUSY",
            "INTERNAL_ERROR",
            "SERVICE_UNAVAILABLE",
            "INVALID_RESPONSE",
            "READBACK_PENDING",
            "REFRESH_PENDING",
          ].includes(e.code),
      );
      void refresh();
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  const submit = (path: string, body: unknown) => {
    const last: Receipt | null = JSON.parse(
      sessionStorage.getItem(storage + ":last") || "null",
    );
    const same =
      last?.path === path &&
      last?.persona === persona &&
      JSON.stringify(last.body) === JSON.stringify(body);
    return run(
      pending ||
        (same ? last! : { path, body, key: crypto.randomUUID(), persona }),
    );
  };
  const feedback = (
    <>
      {success && <Banner tone="good">{success}</Banner>}
      {(error || pending) && (
        <Banner tone={error ? "danger" : "info"}>
          {error ||
            (busy
              ? "Saving and verifying the record…"
              : "An unfinished request was retained. Retry it to confirm the outcome.")}
          {pending && pending.persona !== persona && (
            <p>
              This unfinished request belongs to the {pending.persona} persona.
              Select that simulated persona explicitly to recover it.
            </p>
          )}
          {pending && (
            <div className="button-row">
              <button
                type="button"
                disabled={busy || pending.persona !== persona}
                onClick={() => void run(pending)}
              >
                Retry same request
              </button>
              {revisable && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    sessionStorage.removeItem(storage);
                    setPending(null);
                    setError("");
                    setRevisable(false);
                    void refresh();
                  }}
                >
                  Revise request after denial
                </button>
              )}
            </div>
          )}
        </Banner>
      )}
    </>
  );
  return { submit, busy, pending: !!pending, feedback };
}
