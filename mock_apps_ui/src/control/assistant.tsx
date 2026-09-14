import { useHost, reviewable } from "./host";
import { ConciergeConversation, useConciergeChat } from "./concierge-chat";
import { useEffect, useRef, useState, type CSSProperties } from "react";
import { useLocation } from "react-router-dom";
import { MessageSquare, Mic, Minus, Send, Square } from "lucide-react";
import { useControl } from "./data";
import { useDictation } from "./dictation";
import type { ConciergeRequest } from "./masthead";
import { MODAL_OPEN } from "./dialog";
import "./rethink-utilities.css";

export function Concierge({ openRequest }: { openRequest: ConciergeRequest }) {
  const { pathname, search } = useLocation();
  const { data } = useControl();
  const host = useHost();
  const [open, setOpen] = useState(false),
    [tiny, setTiny] = useState(true);
  const [searchContext, setSearchContext] = useState<Record<string, string>>(
    {},
  );
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [disclosure, setDisclosure] = useState(false),
    [consent, setConsent] = useState(false);
  const handledOpenRequest = useRef(0);
  const launcher = useRef<HTMLButtonElement>(null),
    panel = useRef<HTMLElement>(null),
    composer = useRef<HTMLTextAreaElement>(null);
  const dock = useRef<HTMLDivElement>(null);
  const [lift, setLift] = useState(0);
  const [viewport, setViewport] = useState<CSSProperties>({}),
    [compact, setCompact] = useState(false);
  const parts = pathname.split("/"),
    caseId = parts[4] === "cases" ? parts[5] : undefined;
  const program = data?.programs.find((p) => p.id === parts[3]);
  const scope = pathname.replace(/\/$/, "");
  const chatContext = scope + search;
  const chat = useConciergeChat(chatContext);
  const connected = !!host?.data && !host.error;
  const otherDraft = Object.entries(drafts).find(
    ([key, text]) => key !== scope && !!text.trim(),
  );
  useEffect(() => {
    const body = panel.current?.querySelector<HTMLElement>(
      ".cp-chat-conversation",
    );
    const latest = body?.querySelector<HTMLElement>(
      ".cp-chat-turn:last-of-type",
    );
    if (body && latest)
      body.scrollTop +=
        latest.getBoundingClientRect().top - body.getBoundingClientRect().top;
  }, [chat.turns.at(-1)?.message_id, chat.turns.at(-1)?.status, open]);
  const reviewedProposal =
    pathname.startsWith("/control/decisions/") &&
    host?.data?.proposals.find((p) => p.proposal.proposal_id === parts[3]);
  const evidenceReviewContext = pathname.startsWith(
    "/control/decisions/evidence/",
  );
  const workflowContext =
    pathname.startsWith("/control/workflows") ||
    pathname.startsWith("/control/automations") ||
    pathname.startsWith("/control/runs");
  const selectedConfiguration = host?.data?.automations?.find(
    (a) => a.automation_id === parts[3],
  );
  const selectedWorkflow = host?.data?.workflows?.find(
    (w) => w.workflow_id === parts[3],
  );
  const selectedRun =
    pathname.startsWith("/control/runs/") ||
    pathname.startsWith("/control/operations/runs/")
      ? [
          ...(host?.data?.runs || []),
          ...(host?.data?.standard?.runs || []),
          ...(host?.data?.quality?.runs || []),
          ...(host?.data?.autonomous_quality?.runs || []),
          ...(host?.data?.delivery?.runs || []),
        ].find((r) => r.run_id === parts.at(-1))
      : undefined;
  const context = selectedRun
    ? `${data?.programs.find((p) => p.id === "PRG-A17")?.name || "PRG-A17"} · ${selectedRun.change_id} · Run`
    : workflowContext
      ? selectedConfiguration?.name ||
        selectedWorkflow?.name ||
        "Workflows & Automations"
      : evidenceReviewContext
        ? "CR-017 · Engineering evidence review"
        : reviewedProposal
          ? `${data?.programs.find((p) => p.id === "PRG-A17")?.name || "PRG-A17"} · CR-017 · Proposal review`
          : caseId
            ? `${program?.name || parts[3]} · ${caseId}`
            : program?.name ||
              {
                "/control": "Overview",
                "/control/overview": "Overview",
                "/control/programs": "Programs",
                "/control/workflows": "Workflows & Automations",
                "/control/decisions": "Decisions",
                "/control/scenarios": "Scenarios",
                "/control/knowledge": "Knowledge & Evidence",
                "/control/operations": "Operations",
              }[scope] ||
              "Workspace";
  const write = (key: string, text: string) =>
    setDrafts((all) => ({ ...all, [key]: text }));
  const voice = useDictation(scope, drafts[scope] || "", write);
  const busy = voice.state !== "off";
  const openChat = () => {
    setOpen(true);
    setTiny(false);
    setLift(0);
    composer.current?.focus();
  };
  const close = () => {
    voice.cleanup();
    setDisclosure(false);
    setOpen(false);
    requestAnimationFrame(() => {
      // Do not steal focus if the user has already moved to search or another control.
      const active = document.activeElement;
      if (
        active === document.body ||
        !active ||
        panel.current?.contains(active)
      )
        launcher.current?.focus({ preventScroll: true });
    });
  };
  const mic = () => {
    openChat();
    if (!voice.supported) return;
    if (!consent) setDisclosure(true);
    else voice.start();
  };
  useEffect(() => {
    if (!openRequest.id || openRequest.id === handledOpenRequest.current)
      return;
    // A queued search action must never be applied after its route context changed.
    if (openRequest.context.replace(/\/$/, "") !== scope) return;
    handledOpenRequest.current = openRequest.id;
    voice.cleanup();
    if (openRequest.query) {
      setDrafts((all) => ({
        ...all,
        [scope]: [all[scope], openRequest.query].filter(Boolean).join("\n\n"),
      }));
      setSearchContext((all) => ({
        ...all,
        [scope]: `Added from ${openRequest.origin === "agent" ? "Agent workspace" : "global search"} · ${context}. Existing draft retained.`,
      }));
    }
    openChat();
  }, [openRequest.id, scope]);
  useEffect(() => {
    if (open) composer.current?.focus();
  }, [open]);
  useEffect(() => {
    if (disclosure)
      document.querySelector<HTMLElement>(".cp-voice-disclosure")?.focus();
  }, [disclosure]);
  useEffect(() => {
    setDisclosure(false);
  }, [scope]);
  useEffect(() => {
    const visual = window.visualViewport;
    if (!visual) return;
    const resize = () => {
      const zoom =
        Number.parseFloat(getComputedStyle(document.documentElement).zoom) || 1;
      setCompact(visual.height / zoom <= 600);
      setViewport({
        "--cp-visible-width": `${visual.width / zoom}px`,
        "--cp-visible-height": `${visual.height / zoom}px`,
        "--cp-keyboard-inset": `${Math.max(0, window.innerHeight - visual.height - visual.offsetTop) / zoom}px`,
      } as CSSProperties);
    };
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(document.documentElement);
    visual.addEventListener("resize", resize);
    visual.addEventListener("scroll", resize);
    return () => {
      observer.disconnect();
      visual.removeEventListener("resize", resize);
      visual.removeEventListener("scroll", resize);
    };
  }, [open]);
  useEffect(() => {
    const modal = () => setDisclosure(false);
    window.addEventListener(MODAL_OPEN, modal);
    return () => window.removeEventListener(MODAL_OPEN, modal);
  }, []);
  useEffect(() => {
    const keydown = (event: KeyboardEvent) => {
      if (
        open &&
        event.key === "Escape" &&
        !event.defaultPrevented &&
        !document.querySelector(".cp-root dialog[open]")
      ) {
        event.preventDefault();
        close();
      }
    };
    const revealFocus = () => {
      const target = document.activeElement;
      if (
        !(target instanceof HTMLElement) ||
        !target.matches(
          "a, button, input, select, textarea, summary, [tabindex='0']",
        ) ||
        dock.current?.contains(target) ||
        panel.current?.contains(target) ||
        document.querySelector(".cp-root dialog[open]")
      )
        return;
      const overlay = (
          open ? panel.current : dock.current
        )?.getBoundingClientRect(),
        box = target.getBoundingClientRect();
      if (
        overlay &&
        box.right > overlay.left &&
        box.left < overlay.right &&
        box.bottom > overlay.top &&
        box.top < overlay.bottom
      ) {
        voice.cleanup();
        setDisclosure(false);
        setOpen(false);
        setTiny(true);
        // Preserve page focus, then reveal it above the smaller dock if needed.
        requestAnimationFrame(() => {
          const small = dock.current?.getBoundingClientRect(),
            focused = target.getBoundingClientRect();
          if (
            small &&
            focused.right > small.left &&
            focused.bottom > small.top &&
            focused.top < small.bottom
          )
            setLift(
              (n) =>
                n +
                (small.bottom - focused.top + 12) /
                  (Number.parseFloat(
                    getComputedStyle(document.documentElement).zoom,
                  ) || 1),
            );
        });
      }
    };
    document.addEventListener("keydown", keydown);
    document.addEventListener("focusin", revealFocus);
    window.addEventListener("scroll", revealFocus, true);
    return () => {
      document.removeEventListener("keydown", keydown);
      document.removeEventListener("focusin", revealFocus);
      window.removeEventListener("scroll", revealFocus, true);
    };
  }, [open]);
  const suggestions =
    caseId === "DR-009"
      ? [
          "Can we commit 800 units?",
          "Why are only 600 units available?",
          "What is blocking the remaining 200?",
          "Compare the delivery options.",
          "Is technical readiness complete?",
        ]
      : caseId === "QE-004"
        ? [
            "What do we know about the yield drop?",
            "How much supply is affected?",
            "What do we know versus suspect?",
            "What recovery options are available?",
            "Why can’t the held lot ship?",
          ]
        : caseId === "CR-019"
          ? [
              "Does this request fit the approved scope?",
              "What evidence can be reused?",
              "Has Validation Operations confirmed the handoff?",
              "What remains downstream?",
            ]
          : workflowContext
            ? [
                "What workflows are available?",
                "Which workflows are connected?",
                "Show recent CR-017 runs.",
                "What would this automation do?",
              ]
            : (caseId === "CR-017" || evidenceReviewContext) &&
                host?.data?.downstream?.physical.result
              ? [
                  "Did the validation result close the evidence gap?",
                  "What is the recorded technical outcome?",
                  "Why is customer acceptance still pending?",
                ]
              : caseId === "CR-017"
                ? [
                    "What evidence is missing?",
                    "Compare the validation options.",
                    "What should the operator submit to Engineering?",
                  ]
                : scope.startsWith("/control/knowledge")
                  ? [
                      "Which current documents support this case?",
                      "What is policy versus historical context?",
                      "Show the sources cited by the agents.",
                    ]
                  : scope.startsWith("/control/decisions")
                    ? [
                        "What decisions need my review?",
                        "What changes if this proposal is approved?",
                        "Which evidence supports the recommendation?",
                      ]
                    : scope.startsWith("/control/operations")
                      ? [
                          "Which recorded runs need attention?",
                          "What actions have been confirmed in the source systems?",
                          "Explain the latest investigation outcome.",
                        ]
                      : caseId
                        ? [
                            "Explain this case.",
                            "What are the agents working on?",
                          ]
                        : [
                            "What needs attention?",
                            "What are the agents working on?",
                          ];
  return (
    <div
      className="cp-chat"
      style={
        { ...viewport, "--cp-launcher-lift": `${lift}px` } as CSSProperties
      }
      data-compact={compact}
    >
      {open ? (
        <aside
          ref={panel}
          id="cp-concierge"
          className="cp-chat-window"
          aria-label="Stratos Concierge"
        >
          <header>
            <MessageSquare size={24} aria-hidden="true" />
            <div>
              <h2>Stratos Concierge</h2>
              <span>
                {connected
                  ? "Connected to your workspace"
                  : host?.error
                    ? "Chat backend unavailable"
                    : "Connecting to control host"}
              </span>
            </div>
            <button onClick={close} aria-label="Minimize Stratos Concierge">
              <Minus size={22} />
            </button>
          </header>
          <div className="cp-chat-context">
            <small>Context</small>
            <strong>{context}</strong>
            {host?.data && (
              <small>
                {caseId
                  ? host.data.case_summaries?.find(
                      (c) => c.change_id === caseId,
                    )?.state_label || "Current case state unavailable"
                  : `${host.data.case_summaries?.length ?? 0} connected cases · ${host.data.decision_summaries?.filter((d) => d.requires_human).length ?? 0} decisions need review`}
                {host.error ? " · Stale host read" : ""}
              </small>
            )}
            {searchContext[scope] && <small>{searchContext[scope]}</small>}
            {otherDraft && (
              <small role="status">
                Scope changed. An unsent draft is preserved in the previous
                page; return there to continue it.
              </small>
            )}
          </div>
          <div className="cp-chat-conversation" aria-label="Conversation">
            {!chat.turns.length && (
              <>
                <h3>Ask about {context}</h3>
                <p>
                  {connected
                    ? "Understand the evidence, compare options or clarify the next step."
                    : "Chat backend unavailable. You can prepare a draft; no simulated replies are provided."}
                </p>
              </>
            )}
            <ConciergeConversation chat={chat} context={chatContext} />
            {!chat.turns.length && (
              <div
                className="cp-chat-suggestions"
                aria-label="Suggested questions"
              >
                {suggestions.map((question) => (
                  <button
                    key={question}
                    onClick={() => {
                      voice.cleanup();
                      write(scope, question);
                      composer.current?.focus();
                    }}
                  >
                    {question}
                  </button>
                ))}
              </div>
            )}
          </div>
          <form
            className="cp-chat-compose"
            onSubmit={(e) => {
              e.preventDefault();
              if (busy || !connected || chat.pending) return;
              const text = drafts[scope] || "";
              void chat.send(text).then((sent) => {
                if (sent)
                  setDrafts((all) =>
                    all[scope] === text ? { ...all, [scope]: "" } : all,
                  );
              });
            }}
          >
            {disclosure && (
              <div
                className="cp-voice-disclosure"
                tabIndex={-1}
                role="region"
                aria-label="Before using dictation"
              >
                <strong>Before using dictation</strong>
                <p>
                  Your browser may send audio to its speech provider. Service
                  availability varies. Stratos stores no audio; text stays in
                  this session’s editable draft and is never sent automatically.
                </p>
                <button
                  type="button"
                  className="cp-primary"
                  onClick={() => {
                    setConsent(true);
                    setDisclosure(false);
                    voice.start();
                  }}
                >
                  Start dictation
                </button>
                <button type="button" onClick={() => setDisclosure(false)}>
                  Keep typing
                </button>
              </div>
            )}
            <label htmlFor="cp-chat-draft">Your draft</label>
            <textarea
              id="cp-chat-draft"
              ref={composer}
              rows={3}
              value={drafts[scope] || ""}
              placeholder="Type or dictate a question…"
              aria-describedby="cp-chat-capability"
              onChange={(e) => {
                if (busy) voice.cleanup();
                write(scope, e.target.value);
              }}
            />
            {voice.interim && (
              <p className="cp-voice-interim" aria-live="polite">
                <strong>Interim</strong> {voice.interim}
              </p>
            )}
            <p className="cp-voice-status" role="status">
              {voice.message ||
                (voice.supported
                  ? "Microphone off · Browser dictation"
                  : "Dictation unavailable in this browser. Type your question.")}
            </p>
            <div className="cp-compose-actions">
              {busy ? (
                <>
                  <button
                    type="button"
                    onClick={voice.stop}
                    disabled={voice.state === "stopping"}
                  >
                    <Square size={17} />
                    Stop dictation
                  </button>
                  <button type="button" onClick={voice.cancel}>
                    Cancel dictation
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  onClick={mic}
                  disabled={!voice.supported}
                  aria-label="Dictate to Stratos Concierge"
                >
                  <Mic size={19} />
                  Dictate
                </button>
              )}
              {chat.pending && (
                <button type="button" onClick={() => void chat.stop()}>
                  Stop response
                </button>
              )}
              <button
                disabled={
                  !connected ||
                  busy ||
                  chat.pending ||
                  !(drafts[scope] || "").trim()
                }
                aria-label={
                  connected ? "Send message" : "Send message unavailable"
                }
              >
                <Send size={18} />
                Send
              </button>
            </div>
            <small id="cp-chat-capability">
              {connected
                ? "Send explicitly · Approval requires confirmation · Session-only conversation"
                : "Sending unavailable · Connect the control host"}
            </small>
          </form>
        </aside>
      ) : (
        <div
          className={`cp-concierge-dock ${tiny ? "cp-dock-minimal" : ""}`}
          ref={dock}
        >
          {tiny ? (
            <>
              <button
                ref={launcher}
                onClick={openChat}
                aria-label="Open Stratos Concierge"
              >
                <MessageSquare size={22} />
                Stratos Concierge
              </button>
              <button
                className="cp-minimal-mic"
                onClick={mic}
                disabled={!voice.supported}
                aria-label={
                  voice.supported
                    ? "Dictate to Stratos Concierge"
                    : "Dictation unavailable"
                }
              >
                <Mic size={18} />
              </button>
            </>
          ) : (
            <>
              <div className="cp-dock-heading">
                <MessageSquare size={24} aria-hidden="true" />
                <div>
                  <strong>Stratos Concierge</strong>
                  <small title={context}>{context}</small>
                </div>
                <button
                  aria-label="Reduce Stratos Concierge"
                  onClick={() => {
                    voice.cleanup();
                    setTiny(true);
                  }}
                >
                  <Minus size={18} />
                </button>
              </div>
              <div className="cp-dock-actions">
                <small>
                  Mic off · {connected ? "Connected chat" : "Chat unavailable"}
                </small>
                <button
                  ref={launcher}
                  className="cp-dock-open"
                  onClick={openChat}
                  aria-label="Open Stratos Concierge"
                >
                  Open chat
                </button>
                <button
                  onClick={mic}
                  disabled={!voice.supported}
                  aria-label={
                    voice.supported
                      ? "Dictate to Stratos Concierge"
                      : "Dictation unavailable"
                  }
                >
                  <Mic size={19} />
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
