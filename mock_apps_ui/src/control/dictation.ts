import { useEffect, useRef, useState } from "react";
import { MODAL_OPEN } from "./dialog";

type Result = { isFinal: boolean; [index: number]: { transcript: string } };
export interface BrowserRecognition {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  onstart: (() => void) | null;
  onaudiostart: (() => void) | null;
  onaudioend: (() => void) | null;
  onresult: ((event: { results: ArrayLike<Result> }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  onnomatch: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}
type Constructor = new () => BrowserRecognition;
function recognitionConstructor(): Constructor | undefined {
  const browser = window as unknown as {
    SpeechRecognition?: Constructor;
    webkitSpeechRecognition?: Constructor;
  };
  return browser.SpeechRecognition || browser.webkitSpeechRecognition;
}
const errors: Record<string, string> = {
  "not-allowed":
    "Microphone permission denied. Allow it in browser settings or type instead.",
  "service-not-allowed":
    "Speech service permission denied. Type instead or check browser settings.",
  "audio-capture":
    "No microphone is available. Check your microphone or type instead.",
  "no-speech": "No speech detected. Try again or type instead.",
  network: "Speech service network error. Try again or type instead.",
  aborted: "Dictation interrupted. Your draft is kept; type or try again.",
  "language-not-supported":
    "This speech language is unavailable. Type instead.",
};
export function useDictation(
  scope: string,
  draft: string,
  write: (scope: string, text: string) => void,
) {
  const [state, setState] = useState<
    "off" | "starting" | "listening" | "stopping"
  >("off");
  const [message, setMessage] = useState("");
  const [interim, setInterim] = useState("");
  const latest = useRef({ scope, draft, write });
  latest.current = { scope, draft, write };
  const session = useRef<{
    recognition: BrowserRecognition;
    scope: string;
    base: string;
    final: string;
    timer: ReturnType<typeof setTimeout>;
    stoppingTimer?: ReturnType<typeof setTimeout>;
  } | null>(null);
  const supported = typeof recognitionConstructor() === "function";
  const finish = (text: string, discard = false, notify = true) => {
    const current = session.current;
    session.current = null;
    if (current) {
      clearTimeout(current.timer);
      clearTimeout(current.stoppingTimer);
      const r = current.recognition;
      r.onstart =
        r.onaudiostart =
        r.onaudioend =
        r.onresult =
        r.onerror =
        r.onend =
        r.onnomatch =
          null;
      try {
        r.abort();
      } catch {
        /* Already ended. No retries or background restart. */
      }
      if (discard) latest.current.write(current.scope, current.base);
    }
    if (notify) {
      setState("off");
      setInterim("");
      setMessage(text);
    }
  };
  const start = () => {
    if (session.current || document.querySelector(".cp-root dialog[open]"))
      return;
    const Constructor = recognitionConstructor();
    if (!Constructor) {
      setMessage("Dictation unavailable in this browser. Type your question.");
      return;
    }
    const base = latest.current.draft,
      scope = latest.current.scope;
    let r: BrowserRecognition;
    try {
      r = new Constructor();
    } catch {
      setMessage("Speech service unavailable. Type instead.");
      return;
    }
    const current = {
      recognition: r,
      scope,
      base,
      final: "",
      timer: setTimeout(
        () =>
          finish("60-second limit reached. Review your draft or start again."),
        60000,
      ),
    };
    session.current = current;
    const valid = () =>
      session.current === current && latest.current.scope === scope;
    r.continuous = true;
    r.interimResults = true;
    r.maxAlternatives = 1;
    r.lang = document.documentElement.lang || navigator.language || "en-US";
    r.onstart = () => {
      if (valid())
        setMessage("Speech service connected; waiting for microphone.");
    };
    r.onaudiostart = () => {
      if (valid()) {
        setState("listening");
        setMessage("Listening · Transcription stays in your draft");
      }
    };
    r.onaudioend = () => {
      if (valid()) {
        setState("stopping");
        setMessage("Microphone stopped; finishing transcription…");
      }
    };
    r.onresult = (event) => {
      if (!valid()) return;
      const final: string[] = [],
        pending: string[] = [];
      // The service sends its complete result list, including prior final entries.
      // Rebuild from that list so repeated interim/final callbacks cannot duplicate text.
      Array.from(event.results).forEach((result) =>
        (result.isFinal ? final : pending).push(result[0].transcript.trim()),
      );
      current.final = final.filter(Boolean).join(" ");
      latest.current.write(
        scope,
        [base, current.final]
          .filter(Boolean)
          .join(base.endsWith(" ") || base.endsWith("\n") ? "" : " "),
      );
      setInterim(pending.filter(Boolean).join(" "));
    };
    r.onerror = (event) => {
      if (valid())
        finish(
          errors[event.error] ||
            "Speech service interrupted. Your draft is kept; type or try again.",
        );
    };
    r.onnomatch = () => {
      if (valid())
        finish("Speech wasn’t recognized. Try again or type instead.");
    };
    r.onend = () => {
      if (valid())
        finish(
          current.final
            ? "Dictation added. Review your draft before sending."
            : "No speech recognized. Try again or type instead.",
        );
    };
    setState("starting");
    setInterim("");
    setMessage("Requesting microphone permission…");
    try {
      r.start();
    } catch {
      finish(
        "Speech service could not start. Check permissions or type instead.",
      );
    }
  };
  const stop = () => {
    const current = session.current;
    if (!current) return;
    setState("stopping");
    setMessage("Stopping dictation…");
    try {
      current.recognition.stop();
    } catch {
      finish("Dictation stopped. Your draft is kept.");
      return;
    }
    if (session.current === current)
      current.stoppingTimer = setTimeout(
        () =>
          finish(
            "Speech service interrupted. Final text is kept in your draft.",
          ),
        3000,
      );
  };
  const cancel = () =>
    finish("Dictation canceled. Your original draft is restored.", true);
  const cleanup = () => {
    if (session.current)
      finish("Microphone off. Final text is kept in its original draft.");
  };
  useEffect(() => {
    setMessage("");
    return () => finish("", false);
  }, [scope]);
  useEffect(() => {
    const hide = () => {
      if (document.hidden) cleanup();
    };
    window.addEventListener(MODAL_OPEN, cleanup);
    window.addEventListener("pagehide", cleanup);
    document.addEventListener("visibilitychange", hide);
    return () => {
      window.removeEventListener(MODAL_OPEN, cleanup);
      window.removeEventListener("pagehide", cleanup);
      document.removeEventListener("visibilitychange", hide);
      finish("", false, false);
    };
  }, []);
  return { supported, state, message, interim, start, stop, cancel, cleanup };
}
