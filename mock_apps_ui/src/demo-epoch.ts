// This token invalidates local views/drafts. It carries no business state or authority.
export const DEMO_CHANGED = "stratos:demo-reset";
let epoch: string | null =
  typeof sessionStorage === "undefined"
    ? null
    : sessionStorage.getItem("stratos:demo-epoch");
export const demoEpoch = () => epoch;
export const isAutonomousEpoch = () => epoch?.startsWith("reset_autonomous_") === true;
export function observeDemoEpoch(next: string | null, notify = true) {
  if (!next || next === epoch) return;
  const changed = epoch !== null;
  epoch = next;
  if (typeof sessionStorage !== "undefined")
    sessionStorage.setItem("stratos:demo-epoch", next);
  if (changed) {
    // Existing source UI retry receipts are tab-local drafts, never source records.
    if (typeof sessionStorage !== "undefined")
      for (const key of Object.keys(sessionStorage))
        if (key.startsWith("retry:") || key.startsWith("stratos.workflow-invocation.") || key.startsWith("stratos.standard-invocation.") || key.startsWith("stratos.cr017.invocation") || key.startsWith("stratos.quality.invocation") || ["stratos-cr017-invocation", "stratos.delivery.invocation"].includes(key)) sessionStorage.removeItem(key);
    if (notify && typeof window !== "undefined")
      window.dispatchEvent(new Event(DEMO_CHANGED));
  }
}
