Continue in the existing Stratos Silicon repository and current Phase 10 thread.

Implement a small cosmetic improvement:
ADD SIMPLE MODERN ICONS TO THE PRIMARY NAVIGATION TABS.

This is a visual refinement only.

Do not change:
- navigation destinations
- route structure
- RBAC / persona visibility
- ordering of tabs
- business logic
- workflow behavior
- authorization
- source systems
- Concierge behavior
- page layouts beyond the minimal spacing needed for icons

Preserve all current Phase 10 persona-aware navigation behavior.

==================================================
1. OBJECTIVE
==================================================

Add a small, modern, minimalist icon next to each top-navigation label to improve
visual scanability and make the control plane feel more polished.

Current destinations:

- Overview
- Programs
- Workflows & Automations
- Decisions
- Scenarios
- Knowledge & Evidence
- Operations

The icons should feel:
- modern
- lightweight
- enterprise
- simple
- consistent
- visually aligned with the current Stratos design language

They should support the label, not compete with it.

==================================================
2. ICON STYLE
==================================================

Use the existing icon system/library already installed in the application.

Do not add another icon package unless the repository genuinely has no suitable
icon set.

Preferred characteristics:

- outline / line icons
- approximately 1.5–2px consistent stroke
- rounded or clean geometry
- no filled colorful illustrations
- no emoji
- no gradients
- no custom image assets
- no oversized icons
- no mixed icon styles

Target desktop size:
approximately 16–18px

Keep the text label visible.
Do NOT replace navigation labels with icon-only navigation.

==================================================
3. RECOMMENDED ICON SEMANTICS
==================================================

Choose the closest available icon from the existing library.

Use these concepts rather than forcing exact icon names:

OVERVIEW
Concept:
dashboard / home / overview grid

PROGRAMS
Concept:
layers / portfolio / projects / stacked program objects

WORKFLOWS & AUTOMATIONS
Concept:
workflow / branching arrows / automation / connected nodes

DECISIONS
Concept:
check-circle / decision / approval / clipboard-check

SCENARIOS
Concept:
branching paths / sliders / what-if / route split

KNOWLEDGE & EVIDENCE
Concept:
book / document-search / library / evidence files

OPERATIONS
Concept:
activity / pulse / monitoring / system controls

Choose the icon that best fits the actual installed library and looks most
coherent as a set.

Do not use visually confusing metaphors such as:
- robot icon for Workflows
- dollar sign for Decisions
- generic settings gear for every technical tab

==================================================
4. LAYOUT
==================================================

Navigation item format:

[icon] Label

Use approximately:
- 7–9px gap between icon and text
- existing tab spacing between navigation items
- vertical alignment centered with text

Do not significantly increase nav height.

The active tab should continue using the existing blue underline / selected text
treatment.

The icon should inherit the same visual state as the text:

inactive:
muted navy/gray

active:
current Stratos action blue

hover/focus:
existing interaction color

Do not add colored backgrounds or icon pills to navigation.

==================================================
5. PERSONA / RBAC COMPATIBILITY
==================================================

Use the existing persona-aware navigation list.

Icons should be part of the shared navigation metadata/component so that when a
persona hides a tab, its icon disappears with it.

Do not create a separate hard-coded navigation definition just for icons.

For example:

Program Operator:
Overview · Programs · Workflows & Automations · Decisions · Scenarios ·
Knowledge & Evidence · Operations

Engineering Approver:
only the surfaces permitted by the existing capability matrix

Read-only viewer:
restricted surfaces remain hidden

Icons must follow the same server/client capability projection.

==================================================
6. ACCESSIBILITY
==================================================

Icons are decorative because the visible text already provides the accessible
name.

Therefore:
- hide decorative SVGs from assistive technology where appropriate
- do not duplicate the nav label in accessible text
- preserve existing focus states
- preserve keyboard navigation

If an icon carries unique meaning not contained in the label, reconsider the
design rather than adding hidden explanatory text.

==================================================
7. RESPONSIVE BEHAVIOR
==================================================

Preserve current responsive navigation behavior.

At narrower widths:
- icons must not cause clipping
- labels should continue to behave according to the existing responsive design
- do not introduce horizontal overflow solely because icons were added

If the current design already collapses or scrolls navigation, preserve that.

Do not create icon-only mobile navigation in this task.

==================================================
8. VISUAL REVIEW
==================================================

Review the full set together.

The seven icons should feel like one family.

Check:
- consistent optical size
- stroke weight
- vertical alignment
- spacing
- active/inactive states

Avoid a situation where one icon visually dominates the others.

Use visual judgment rather than mechanically selecting the first matching icon.

==================================================
9. TESTING
==================================================

Run:
- relevant navigation/component tests
- persona/RBAC navigation tests
- browser smoke at 1440x900 and 1280x800
- typecheck
- production build

Verify:
- all permitted navigation still works
- hidden tabs remain hidden for restricted personas
- icons do not alter route behavior
- active state stays synchronized with route
- keyboard navigation still works
- no layout overflow/regression

No paid model calls.

==================================================
10. REPORT
==================================================

Report:

1. Icon library reused
2. Exact icon chosen for each tab
3. Files changed
4. Persona/RBAC compatibility
5. Screenshots at 1440x900
6. Tests/results

Stop after this cosmetic navigation refinement.
Do not make unrelated Phase 10 changes.
## Additional direct user request in the same message

“Also, ‘Needs attention’ section need to be grouped into a similar box as ‘Agent workspace’ as well. Put ‘Programs’ right underneath ‘Overview’. Move ‘Agent workspace’ and ‘Needs attention’ underneath ‘Programs’.”

This explicitly expands the cosmetic scope to the Overview section order and matching panel treatment. Preserve the Overview summary and business content.
