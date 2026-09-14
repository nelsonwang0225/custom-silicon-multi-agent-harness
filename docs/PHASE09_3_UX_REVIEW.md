# Phase 09.3 — Initial browser review

Reviewed the existing connected app in Chromium at 1440×900, with isolated
`.cache/phase09-3/review/` source and metadata storage, real local HTTP/MCP and
existing deterministic model doubles. No paid model or real microphone was used.
The tour covered 24 surfaces before component edits: Overview, Program, four
cases before/after investigation, Workflows, Decisions, Operations, search,
alerts, persona selection, evidence, Engineering/Manufacturing source links and
floating Concierge. Initial captures included transient loading; a second tour
waited for settled reads. Raw screenshots/observations are retained in
`.cache/phase09-3/before/`.

## Material findings

1. Overview's large hero and three program cards push attention and agent activity
   below the 900-pixel viewport. Program puts agent definitions and a milestone
   ahead of the four canonical cases, which require several screens of scrolling.
2. The shared case-state panel precedes the case heading/breadcrumb, followed by
   duplicate workflow status and host metadata. The business question and next
   decision compete with source IDs, disclaimers and refresh controls.
3. CR-017's eight-stage prose-heavy tracker and command hero hide the evidence
   comparison. QE percentages lack a visual baseline comparison. DR's reconciled
   inventory graphic is several sections below the heading. CR-019's policy
   checklist is useful but reads like an implementation audit.
4. The resting Concierge is 440×163 pixels and covers primary content/actions.
   Its open context repeats CR-017-specific implementation wording even on the
   multi-case Program page. Cards and confirmations need clearer ownership.
5. The active identity becomes an avatar. The selector lists roles but not their
   responsibilities; its footer incorrectly calls persona switching a read-only
   preview. Disabled actions often require interpreting nearby prose.
6. Decisions lead with versions/IDs and implementation terminology, while exact
   business consequences are deeper. QE/DR case decision links need a direct
   route to the existing consequential review section.
7. Operations leads with verbose context and filter controls; raw IDs/time/tool
   detail should remain accessible without dominating the business outcome.
8. Search contains the right business records but result metadata is noisy.
   Alerts repeat source/state wording instead of a concise case + action label.
9. Evidence dialogs already have sound native modality and two-column layout.
   Preserve focus/escape behavior, strengthen applicability/coverage first, and
   keep provenance available. Existing source apps remain the authority.

## Chosen scope

Retain Stratos blue/neutral styling and the existing routes. Build a shared
business-first case header, actual-progress tracker and source-backed visuals;
compact Program case cards and Overview composition; truthful recorded-agent
cards; role descriptions/direct switch guidance; concise exact decisions;
progressive disclosure of technical detail; a smaller resting Concierge with a
roomier focused conversation. Keep every approval, source write, reset and voice
consent boundary unchanged. No new Quality release persona or authority exists:
Program Owner reviews bounded recovery metadata; Manufacturing owns disposition.
