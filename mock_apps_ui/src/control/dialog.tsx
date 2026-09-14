import { useEffect, useId, useRef, type ReactNode } from "react";
import { X } from "lucide-react";

// Synchronous notification: microphone capture must end BEFORE showModal makes the page inert.
export const MODAL_OPEN = "stratos:modal-opening";
export function Dialog({
  title,
  close,
  children,
  footer,
  closeLabel = "Close preview",
  note = "Read-only preview",
  showDone = true,
  className = "",
}: {
  title: string;
  close: () => void;
  children: ReactNode;
  footer?: ReactNode;
  closeLabel?: string;
  note?: string;
  showDone?: boolean;
  className?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const heading = useId();
  const prior = useRef(document.activeElement as HTMLElement);
  const closeRef = useRef(close);
  closeRef.current = close;
  useEffect(() => {
    const dialog = ref.current!;
    // Never stack modals. A second programmatic request is dismissed safely.
    if (document.querySelector(".cp-root dialog[open]")) {
      closeRef.current();
      return;
    }
    window.dispatchEvent(new Event(MODAL_OPEN));
    const scroll = { x: window.scrollX, y: window.scrollY };
    const overflow = document.body.style.overflow;
    dialog.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      dialog.close();
      document.body.style.overflow = overflow;
      const target =
        prior.current?.isConnected && prior.current !== document.body
          ? prior.current
          : document.getElementById("cp-main");
      target?.focus({ preventScroll: true });
      window.scrollTo(scroll.x, scroll.y);
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={`cp-modal ${className}`}
      aria-labelledby={heading}
      aria-modal="true"
      onKeyDown={(event) => {
        if (event.key !== "Tab") return;
        // Native modality makes the page inert, but some browsers still tab to
        // browser chrome at the boundary. Keep keyboard navigation in this task.
        const controls = Array.from(
          event.currentTarget.querySelectorAll<HTMLElement>(
            "a[href], button, input, select, textarea, summary, [tabindex]",
          ),
        ).filter(
          (element) =>
            element.tabIndex >= 0 &&
            !element.matches(":disabled") &&
            element.getClientRects().length > 0,
        );
        const first = controls[0],
          last = controls.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }}
      onCancel={(e) => {
        e.preventDefault();
        closeRef.current();
      }}
    >
      <header>
        <h2 id={heading}>{title}</h2>
        <button autoFocus onClick={close} aria-label={closeLabel}>
          <X size={22} />
        </button>
      </header>
      <div className="cp-modal-body">{children}</div>
      <footer>
        <span>{note}</span>
        <div>
          {footer}
          {showDone && <button onClick={close}>Done</button>}
        </div>
      </footer>
    </dialog>
  );
}
