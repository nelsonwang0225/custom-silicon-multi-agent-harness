# Phase 10.1 — Persona access contract

The [Phase 10.1 request](../prompts/10_1_PERSONA_ACCESS.md) supersedes earlier instructions that exposed all seven workspaces to every display profile. This is a local demo capability projection, not authentication or enterprise IAM. Four existing trusted host actors and source authority remain unchanged.

## Presentation matrix

| Surface | Program operator | Engineering approver | Program Owner | Read-only viewer |
|---|---|---|---|---|
| Overview | Show | Show | Show | Show |
| Programs and scoped case facts | Show | Show | Show | Show |
| Workflows & Automations | Show | Hide | Hide | Hide |
| Decisions queue | Read/track all | Validation authorization and evidence review | QE recovery and DR commitment | Hide |
| Scenarios | All four | CR-017, CR-019 | QE-004, DR-009 | Hide |
| Knowledge & Evidence | Show | Show | Hide | Show |
| Operations | Limited | Hide | Hide | Hide |

“Limited Operations” means the existing A17 scoped run/activity, source health and allowlisted evaluation/artifact projections, with only the selected operator's retained Concierge sessions. Other actors' sessions and legacy sessions with no recorded owner are excluded; guessing their IDs does not grant access. Historical files are retained. No new raw-artifact access, orchestration or scheduler is installed.

## Existing business authority, independent of workspace access

| Action | Operator `demo-automation` | Engineering `demo-engineer` | Owner `demo-program-owner` | Viewer `demo-reader` |
|---|---|---|---|---|
| CR-017 case investigation | Yes | Yes | Yes, existing scoped endpoint | No |
| CR-017 manual proposal preparation | Yes | Yes | No | No |
| CR-017 exact plan approve/reject | No | Yes | No | No |
| CR-017 exact approved execution/recovery | Yes | Yes | No | No |
| CR-017 downstream result reassessment | Yes | Yes | No | No |
| CR-017 exact engineering evidence review | No | Yes | No | No |
| CR-019 investigation; intake reconciliation/retry | Yes | Yes | No | No |
| QE-004 / DR-009 investigation | Yes | Yes | Yes | No |
| QE recovery / DR commitment approve/reject | No | No | Yes | No |
| QE / DR exact approved execution | Yes | No | Yes | No |
| QE / DR explicit reconciliation endpoint | Yes | No | No | No |
| Save automation configuration metadata | Yes | Yes, scoped Concierge / existing API | No | No |
| Explanatory Concierge Q&A | Yes | Yes | Yes | Yes |
| Demo reset | Separate maintenance gate | No | No | No |

Two older runbook descriptions were narrower than implemented server authority: Engineering already could investigate QE/DR, and Program Owner already could investigate CR-017 through its case endpoint (which admitted selected non-readers). Preserve those paths. The generic workflow invocation endpoint retains its original operator/engineering rule. Hiding its catalog does not remove an engineer's case investigation, or grant Program Owner generic invocation.

Engineering's existing automation configuration write remains available through scoped Concierge and its exact confirmation. Engineering cannot browse the top-level configuration store. Confirmation replies link back to the permitted case/program. Configuration is metadata only; schedules/events/conditions stay inactive.

CR-019 retains deterministic bounded Validation Operations intake without a new human approval. CR-017 plan authorization and later evidence review are distinct. QE review permits recovery metadata, never material release/disposition or established root cause. DR review permits the exact ERP commitment and Planner link, never allocation, technical acceptance or customer agreement. No persona switch performs an approval, execution or model call. Source services retain exact versions, manifests, idempotency, freshness and independent readback checks.

## Shared projection and scoped reads

`control_host/access.py` resolves only the installed actor singletons and projects surface access, explicit scenario/decision categories and action permissions. `GET /control-api/capabilities` is generated into the TypeScript host schema. Missing selection uses a non-mutating reader view; unknown profiles and unsupported capability scopes fail closed. Client booleans are never accepted as authority.

The browser uses this projection for navigation, route guards, shared links, action rendering, queue filtering, search/alerts and review counts. Loading does not render restricted destinations. Denied routes go to Overview. No permission means no rendered control; a permitted but stale, busy, incomplete or unapproved action remains disabled with a readiness explanation. Case outcomes and the responsible role remain readable.

The host protects Workflows/Automations reads, the dedicated Decisions queue, run/Operations APIs and session reads. The four scoped case endpoints retain business summaries, exact source evidence, recorded decisions, run outcomes and activity. Their trace identifiers are removed, and non-operator snapshots omit workspace configuration/catalog data. Disallowed exact-decision links resolve to permitted case facts instead. The queue endpoint filters by source-backed decision kind; case-level summaries may cover all four cases because business read scope remains intact.

Program health uses the same source facts for every persona. Only review counts and attention ordering change: count a current proposal requiring this actor's review, never another role's work. The four installed scenario IDs determine technical/business categories; titles are not classifiers.

Concierge resolves context permission before the manager call, passes effective capabilities and only same-owner session history, and reads filtered business projections. Disallowed action intents return explanation/navigation without action tokens or workflow admission. Preview tokens, polling, cancellation and confirmation belong to their originating actor. Confirmation still calls existing host handlers and revalidates current source authority. Successful confirmation links are filtered too. Concierge has no tool for persona switching, reset or reading another person's transcript.

## Switching and environment limits

An explicit selector change remounts scoped providers and views, discards local drafts, forms, dialogs, search/alerts and pending action previews, stops polling/voice capture, and generates a new visible chat session. Old responses cannot update the new persona's view or trigger follow-up actions. Scoped invocation retry IDs are cleared; source-app retry state is separate. Already admitted work and immutable approvals retain their original attribution and are not revoked or cancelled.

The selector exposes public synthetic identities; anyone operating this local demo can explicitly choose one. Actor-bound sessions separate demo personas, not authenticated people sharing a persona. Legacy ownerless transcripts are unavailable through HTTP because ownership cannot safely be inferred.

Source-app links/previews retain their existing source scope and independent public demo selectors. Fixed source read identities, allowlisted documents and source API permission checks are unchanged. Hiding Knowledge from Program Owner does not hide the source evidence needed for QE/DR case review. This change does not secure the independently accessible five source apps or migrate their authentication. Existing portfolio source reads can show their installed programs; host actions remain bound to CUST-FML01 / PRG-A17 and the four installed cases.

Reset remains the existing deliberate host-only maintenance operation. The browser requires selected operator plus the separate maintainer gate; the local maintenance CLI retains its existing gate without requiring a business selector. Other selected profiles are refused even with a maintenance token. No agent reset tool is exposed.

See [handoff and verification](PHASE10_1_HANDOFF.md) and the [runbook](DEMO_RUNBOOK.md).
