import { useEffect, useRef, useState } from "react";
import { traceStatus } from "./trace-language";
import { Link } from "./access";
import { call, hostError, useHost, type HostSchema } from "./host";

type Turn = HostSchema["Turn"];
type Card = HostSchema["Card"];
type Body = HostSchema["ChatRequest"];
const id = (prefix: string) => prefix + crypto.randomUUID().replaceAll("-", "");

export function useConciergeChat(context: string) {
  const host = useHost();
  const [session] = useState(() => id("chat_"));
  const [turns, setTurns] = useState<Turn[]>([]);
  const [error, setError] = useState("");
  const [retryBody, setRetryBody] = useState<Body | null>(null);
  const [sending, setSending] = useState(false);
  const lock = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const update = (turn: Turn) =>
    mounted.current &&
    setTurns((old) =>
      [...old.filter((t) => t.message_id !== turn.message_id), turn]
        .sort((a, b) => a.created_at.localeCompare(b.created_at))
        .slice(-24),
    );
  const send = async (text: string, retry?: Body) => {
    if (!mounted.current || lock.current || !text.trim()) return false;
    lock.current = true;
    setSending(true);
    setError("");
    const body = retry || {
      session_id: session,
      message_id: id("msg_"),
      context,
      text,
    };
    try {
      update(
        await call<Turn>("/concierge/messages", host?.profile || null, body),
      );
      setRetryBody(null);
      return true;
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e));
      setRetryBody(body);
      return false;
    } finally {
      lock.current = false;
      setSending(false);
    }
  };
  const running = turns.filter((t) => t.status === "running");
  useEffect(() => {
    if (!running.length) return;
    let stopped = false,
      polling = false;
    const poll = async () => {
      if (polling) return;
      polling = true;
      try {
        for (const t of running) {
          const value = await call<Turn>(
            `/concierge/${session}/${t.message_id}`,
            host?.profile || null,
          );
          if (!stopped) {
            update(value);
            if (value.status === "completed" && value.classification === "RUN")
              void host?.refresh();
          }
        }
      } catch (e) {
        if (!stopped) setError(String(e instanceof Error ? e.message : e));
      } finally {
        polling = false;
      }
    };
    const timer = setInterval(() => void poll(), 900);
    return () => {
      stopped = true;
      clearInterval(timer);
    };
  }, [running.map((t) => t.message_id).join(), host?.profile]);
  const stop = async () => {
    for (const t of running) {
      try {
        update(
          await call<Turn>(
            `/concierge/${session}/${t.message_id}/cancel`,
            host?.profile || "reader",
            { context: t.context, confirmed: true },
          ),
        );
      } catch (e) {
        setError(String(e instanceof Error ? e.message : e));
      }
    }
  };
  return {
    session,
    turns,
    send,
    stop,
    pending: sending || !!running.length,
    error,
    retry:
      retryBody && retryBody.context === context
        ? () => send(retryBody.text, retryBody)
        : null,
  };
}

const safeLink = (path: string) =>
  /^\/(control|engineering|validation|manufacturing|erp|programs)(\/|\?|#|$)/.test(
    path,
  ) &&
  !path.includes("\\") &&
  !path.includes("//");
export function ConciergeCard({
  card,
  session,
  context,
  active,
}: {
  card: Card;
  session: string;
  context: string;
  active: boolean;
}) {
  const host = useHost();
  const [current, setCurrent] = useState(card),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [receipt, setReceipt] = useState<{
    text: string;
    cards: Card[];
  } | null>(null);
  const lock = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => setCurrent(card), [card]);
  useEffect(() => {
    if (!card.run_id) return;
    let stopped = false,
      polling = false;
    const poll = async () => {
      if (polling) return;
      polling = true;
      try {
        const next = await call<Card>(
          "/concierge-runs/" + encodeURIComponent(card.run_id!),
          host?.profile || null,
        );
        if (!stopped) {
          setCurrent(next);
          if (
            (next.facts || []).some(
              ([key, val]) => key === "Runtime" && val !== "running",
            )
          )
            clearInterval(timer);
        }
      } catch {
        if (!stopped) {
          setError(
            "Run status unavailable. Open the run to inspect its current state.",
          );
          clearInterval(timer);
        }
      } finally {
        polling = false;
      }
    };
    const timer = setInterval(() => void poll(), 1500);
    void poll();
    return () => {
      stopped = true;
      clearInterval(timer);
    };
  }, [card.run_id, host?.profile]);
  const confirm = async () => {
    if (!mounted.current || lock.current || !active || !card.action_id) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      setReceipt(
        await call(
          `/concierge/${session}/actions/${card.action_id}`,
          host?.profile || null,
          { context, confirmed: true },
        ),
      );
      await host?.refresh();
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e));
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  const summaryCard =
    current.kind === "status" &&
    !card.action_id &&
    current.facts?.some(([key]) => key === "Current source");
  const primaryFacts = (current.facts || []).filter(
    ([key]) =>
      !summaryCard ||
      ["Current source", "Next step", "Root cause"].includes(key),
  );
  const moreFacts = summaryCard
    ? (current.facts || []).filter(
        ([key]) => !["Current source", "Next step", "Root cause"].includes(key),
      )
    : [];
  return (
    <article className={`cp-chat-card cp-chat-card-${current.kind}`}>
      <small>
        {current.kind === "action" || current.kind === "decision"
          ? "Governed action preview"
          : current.kind}
      </small>
      <h4>{current.title}</h4>
      {!!current.facts?.length && (
        <dl>
          {primaryFacts.map(([key, value], i) => (
            <div key={i}>
              <dt>
                {key === "Runtime"
                  ? "Investigation"
                  : key === "Verification"
                    ? "Source confirmation"
                    : key}
              </dt>
              <dd>
                {[
                  "Runtime",
                  "Verification",
                  "Policy route",
                  "Current case state",
                ].includes(key)
                  ? traceStatus(value)
                  : value}
              </dd>
            </div>
          ))}
        </dl>
      )}
      {!!moreFacts.length && (
        <details>
          <summary>Source details ({moreFacts.length})</summary>
          <dl>
            {moreFacts.map(([key, value], i) => (
              <div key={i}>
                <dt>{key}</dt>
                <dd>
                  {key === "Current case state" ? traceStatus(value) : value}
                </dd>
              </div>
            ))}
          </dl>
        </details>
      )}
      <div className="cp-chat-links">
        {(current.links || [])
          .filter((l) => safeLink(l.href))
          .map((l, i) => (
            <Link to={l.href} key={i}>
              {l.label} <span aria-hidden="true">↗</span>
            </Link>
          ))}
      </div>
      {card.required_role && (
        <p className="cp-chat-authority">
          Concierge: analyze / prepare · Required:{" "}
          {card.required_role
            .replace(/\bautomation\b/g, "Program operator")
            .replace(/\bengineer\b/g, "Engineering approver")
            .replace(/\bprogram_owner\b/g, "Program Owner")}{" "}
          · Execution: host-controlled
        </p>
      )}
      {card.action_id && !receipt && (
        <button
          className="cp-primary"
          onClick={() => void confirm()}
          disabled={busy || !active}
        >
          {busy ? "Checking authority…" : card.action_label}
        </button>
      )}
      {!active && card.action_id && (
        <small>
          Context changed. Return to the original scope to review this action.
        </small>
      )}
      {error && (
        <p role="alert" className="cp-error">
          {error}
        </p>
      )}
      {receipt && (
        <div role="status">
          <p>{receipt.text}</p>
          {receipt.cards.map((c, i) => (
            <ConciergeCard
              key={i}
              card={c}
              session={session}
              context={context}
              active={active}
            />
          ))}
        </div>
      )}
    </article>
  );
}

export function ConciergeConversation({
  chat,
  context,
}: {
  chat: ReturnType<typeof useConciergeChat>;
  context: string;
}) {
  return (
    <>
      {chat.turns.map((turn) => (
        <section
          className="cp-chat-turn"
          key={turn.message_id}
          aria-label="Conversation turn"
        >
          <p className="cp-chat-user">{turn.user_text}</p>
          {turn.context !== context && (
            <small>
              Earlier context ·{" "}
              <Link to={turn.context}>Return to that scope</Link>
            </small>
          )}
          <div aria-live="polite">
            <p>
              {turn.status === "running" ? "Reading your request…" : turn.text}
            </p>
          </div>
          {turn.error_code && (
            <p role="alert" className="cp-error">
              {hostError(turn.error_code)}
            </p>
          )}
          {turn.status !== "running" && (
            <small>
              {turn.classification} ·{" "}
              {new Date(turn.created_at).toLocaleTimeString()} ·{" "}
              {turn.status === "completed"
                ? "Read at response time; actions recheck current source"
                : turn.status}
            </small>
          )}
          {(turn.cards || []).map((card, i) => (
            <ConciergeCard
              key={turn.message_id + "_" + i}
              card={card}
              session={chat.session}
              context={turn.context}
              active={turn.context === context}
            />
          ))}
        </section>
      ))}
      {chat.error && (
        <p role="alert" className="cp-error">
          {chat.error}
        </p>
      )}
      {chat.retry && (
        <button onClick={() => void chat.retry?.()}>Retry same request</button>
      )}
    </>
  );
}
