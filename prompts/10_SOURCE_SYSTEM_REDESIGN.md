Continue working in the existing Stratos Silicon repository.

This task is a focused redesign and IMPLEMENTATION of the FIVE SYNTHETIC
ENTERPRISE SOURCE SYSTEMS.

Do NOT redesign the main Stratos Agentic Control Plane in this task.

The goal is to make the five mock enterprise applications feel much more like
credible real-world semiconductor enterprise systems while preserving ALL
existing APIs, data contracts, behaviors, IDs, workflows, source ownership,
agent integrations, MCP tools, RAG behavior, demo functionality, governance,
and connected use cases.

You are authorized to directly modify the source-system UI implementation.

Do NOT wait for approval after proposing a design.

The required workflow is:

RESEARCH
→ INSPECT CURRENT IMPLEMENTATION
→ DESIGN
→ IMPLEMENT DIRECTLY
→ RUN REGRESSION TESTS
→ CAPTURE BEFORE/AFTER
→ REPORT RESULTS

==================================================
1. CORE OBJECTIVE
==================================================

Refine the visual design, information architecture, navigation, page composition,
tables, object-detail views, forms, dashboards, and interaction patterns of the
five source applications so that each one immediately resembles the type of real
enterprise system it represents.

The five source systems should feel DIFFERENT from one another because they
represent different categories of enterprise software.

Someone familiar with enterprise applications should be able to look at each app
and immediately infer:

"This is a PLM."

"This is a validation/test operations system."

"This is an MES / semiconductor manufacturing quality system."

"This is an ERP."

"This is a program / portfolio / NPI planning system."

At the same time:

- keep the experience modern;
- keep it visually clean;
- reduce unnecessary words;
- use strong visual hierarchy;
- use progressive disclosure;
- retain realistic enterprise data density;
- maintain excellent demo usability.

Do NOT turn the apps into legacy-software parodies.

Think:

REALISTIC ENTERPRISE APPLICATION
+
MODERN MINIMALIST PRESENTATION.

==================================================
2. HARD FUNCTIONAL CONSTRAINTS
==================================================

DO NOT CHANGE:

- API endpoint paths
- request schemas
- response schemas
- backend data models
- existing record IDs
- source ownership
- source-of-truth rules
- workflow behavior
- agent behavior
- MCP tools
- RAG behavior
- approval rules
- authority boundaries
- permissions
- deterministic calculations
- reset semantics
- automation semantics
- orchestration behavior
- business conclusions
- golden-path fixture facts

The existing agents must continue reading and writing the same source-system data.

This task is primarily:

UI
+
UX
+
information architecture
+
navigation
+
presentation
+
realistic enterprise-system framing.

If cosmetic display changes require small frontend-only adaptations, implement
them safely.

Do not silently alter backend contracts to make the UI easier.

==================================================
3. SOURCE SYSTEM DISPLAY NAMES
==================================================

Use these names in the UI:

1. Stratos PLM
   Product Lifecycle & Engineering Change

2. Stratos TestOps
   Validation & Qualification

3. Stratos MES
   Manufacturing & Quality

4. Stratos ERP
   Commercial, Orders & Supply

5. Stratos ProgramOps
   Program Planning & Readiness

If internal service names currently use:

Engineering Hub
Validation Lab
Manufacturing Portal
Commercial ERP
Program Planner

DO NOT rename internal packages, APIs, routes, persistence keys, MCP tool names,
or identifiers solely for cosmetic consistency.

Prefer UI display-label changes.

Maintain backward compatibility.

==================================================
4. REAL-WORLD APPLICATION ARCHETYPES
==================================================

Use real enterprise software as DESIGN and INFORMATION-ARCHITECTURE references.

Do NOT clone exact proprietary interfaces, logos, assets, or brand styling.

--------------------------------------------------
A. STRATOS PLM
--------------------------------------------------

Category:
Product Lifecycle Management
Engineering Change Management
Requirements / Configuration Management

Real-world analogues:

- Siemens Teamcenter
- PTC Windchill
- Siemens Polarion
- Jama Connect
- semiconductor internal engineering portals

The UI should communicate:

- product/configuration hierarchy
- controlled engineering objects
- requirements
- change requests
- revisions
- baselines
- applicability
- affected configurations
- documents
- relationships
- status/history

This should feel like a structured engineering-record system.

--------------------------------------------------
B. STRATOS TESTOPS
--------------------------------------------------

Category:
Validation Operations
Test / Lab Management
Qualification
Test Evidence Management

Real-world analogues:

- NI SystemLink
- semiconductor validation portals
- characterization systems
- qualification systems
- internal silicon validation infrastructure

The UI should communicate:

- validation jobs
- test plans
- samples
- configurations
- test stations/resources
- scheduling
- execution state
- procedures
- results
- evidence
- qualification coverage

--------------------------------------------------
C. STRATOS MES
--------------------------------------------------

Category:
Manufacturing Execution System
Quality Management
Yield
Genealogy
Lot Tracking

Real-world analogues:

- Siemens Opcenter Execution Semiconductor
- Applied Materials-style manufacturing/yield systems
- semiconductor fab portals
- OSAT/test operations portals
- manufacturing quality systems

The UI should communicate:

- lots
- units
- manufacturing/test stage
- genealogy
- quantities
- first-pass yield
- baseline yield
- holds
- exceptions
- dispositions
- traceability
- quality state

--------------------------------------------------
D. STRATOS ERP
--------------------------------------------------

Category:
Enterprise Resource Planning
Order Management
Inventory
Supply
Commercial Operations

Primary analogue:

- SAP S/4HANA
- SAP Fiori

Secondary:

- Oracle ERP Cloud
- Oracle SCM
- enterprise order-management systems

This should be the most immediately recognizable business-enterprise system.

The UI should communicate:

- customer orders
- demand
- requested quantity/date
- inventory
- allocations
- eligible supply
- commercial status
- commitments
- customer/account

Think in terms of:

business object
→ object header
→ summary
→ tabs
→ line items
→ status
→ related objects/actions

--------------------------------------------------
E. STRATOS PROGRAMOPS
--------------------------------------------------

Category:
Program Management
Portfolio Management
NPI Planning
Milestone / Dependency Management

Real-world analogues:

- Planisware
- Microsoft Project
- Jira Advanced Roadmaps
- Smartsheet
- Primavera
- semiconductor internal NPI/program tools

The UI should communicate:

- program
- portfolio
- stage/gate
- milestones
- dependencies
- owner
- target dates
- status
- risk
- actions
- recovery work
- readiness

==================================================
5. RESEARCH BEFORE IMPLEMENTING
==================================================

Use web research first.

Study current design and information-architecture patterns from:

- SAP Fiori / S/4HANA
- Siemens Teamcenter
- PTC Windchill
- NI SystemLink
- Siemens Opcenter Semiconductor
- Planisware
- modern enterprise workflow products

Focus on:

- navigation
- object-detail composition
- master/detail behavior
- headers
- tables
- filtering
- search
- tabs
- side panels
- hierarchy/tree views
- process/state representation
- timelines
- command bars
- data density
- relationship views
- audit/history presentation

Do NOT recreate any product pixel-for-pixel.

Extract the category conventions.

Also apply modern minimalist principles inspired by high-quality contemporary
software such as OpenAI and Apple:

- strong hierarchy
- purposeful whitespace
- restrained color
- clear typography
- minimal unnecessary copy
- progressive disclosure
- contextual actions
- predictable interaction
- accessibility
- calm visual rhythm

==================================================
6. MODERN MINIMALIST DESIGN PRINCIPLES
==================================================

The design target is NOT:

"Make SAP look like ChatGPT."

It is:

"Make a believable modern ERP that an enterprise user recognizes structurally,
while making it cleaner and easier to understand."

Apply the equivalent principle to all five systems.

Prioritize:

- simplicity over clutter
- strong hierarchy
- readable density
- progressive disclosure
- visual state over explanatory prose
- one obvious primary action where possible
- concise labels
- contextual actions
- meaningful icons
- calm colors
- consistent spacing
- accessible status representation

Ask for every element:

1. Does the user need this immediately?
2. Does it belong in the header?
3. Should it be in a table?
4. Should it live in a detail tab?
5. Should it move to a side panel/modal?
6. Can the information be made visual?
7. Does this resemble the enterprise application category being modeled?
8. Is it duplicated elsewhere?
9. Can it be stated with fewer words?

Avoid:

- walls of text
- excessive cards
- excessive badges
- excessive borders
- tiny text
- rainbow dashboards
- decorative charts
- fake AI effects
- giant explanatory panels
- generic SaaS layouts reused across all five apps

==================================================
7. EACH APP MUST FEEL DISTINCT
==================================================

This is critical.

Do not make the five apps feel like five datasets rendered through the same
frontend template.

Create a subtle common Stratos family identity, but use category-specific
information architecture.

PLM:
hierarchies, revisions, requirements, change objects, related engineering data.

TestOps:
jobs, samples, plans, resources, test lifecycle, evidence/results.

MES:
lots, quality state, yield, process stage, hold/disposition, genealogy.

ERP:
business objects, orders, line items, inventory, allocations, commitments.

ProgramOps:
portfolio, timeline, milestones, dependencies, risk, ownership.

Do NOT use the exact same dashboard composition in all five systems.

==================================================
8. SHARED STRATOS FAMILY LANGUAGE
==================================================

The systems may share:

- Stratos wordmark
- system font stack
- subtle design tokens
- consistent icon family
- global demo identity
- application switcher if already appropriate
- consistent accessibility behavior

But each source app should have a distinct operational character.

Keep visual differences subtle and professional.

No five-color rainbow suite.

==================================================
9. IMPLEMENT STRATOS PLM
==================================================

Redesign the former Engineering Hub as:

STRATOS PLM
Product Lifecycle & Engineering Change

Suggested navigation where supported:

Home
Products
Configurations
Requirements
Changes
Documents

Do not invent unsupported backend capabilities.

The PLM landing page should emphasize:

- active changes
- current configurations
- affected requirements
- revisions
- controlled documents
- current status

CR-017 and CR-019 should appear as proper engineering change objects.

Representative change page:

CR-017
Material workload change

Header:
Status
Program
Owner
Affected product/config
Revision
Change type

Then sections/tabs as supported:

Overview
Requirements
Impact
Configuration
Documents
History

Represent relationships visually where useful:

Requirement
↓
Configuration
↓
Change
↓
Validation impact

Long prose should be secondary.

The user should feel they are inspecting controlled engineering lifecycle data.

==================================================
10. IMPLEMENT STRATOS TESTOPS
==================================================

Redesign the former Validation Lab as:

STRATOS TESTOPS
Validation & Qualification

Suggested navigation where supported:

Overview
Validation Jobs
Test Plans
Samples
Results
Resources

The landing page should feel operational.

Prioritize:

Scheduled
Running
Completed
Blocked

Validation-job detail should surface:

Job
Status
Sample
Configuration
Procedure
Resource/environment
Schedule
Result

Use a visual lifecycle when supported:

Requested
→ Scheduled
→ Running
→ Result available
→ Reviewed

Preserve semantic truth:

scheduled ≠ executed
executed ≠ passed
passed ≠ engineering approval
engineering approval ≠ customer acceptance

Results should surface:

result state
key metrics
evidence artifact
procedure/version
timestamp

Do not over-explain.

==================================================
11. IMPLEMENT STRATOS MES
==================================================

Redesign the former Manufacturing Portal as:

STRATOS MES
Manufacturing & Quality

Suggested navigation:

Operations
Lots
Quality
Yield
Exceptions

Use existing supported data.

The landing page should immediately feel like semiconductor manufacturing.

Prioritize:

- active lots
- held material
- yield exceptions
- quality records
- latest manufacturing/test state

Example:

LOT-B-204
250 units
HOLD

First-pass yield
80%

Comparable baseline
96%

Δ -16 pts

The lot-detail page should prioritize:

Lot
Product/config
Quantity
Manufacturing/test stage
Yield
Hold status
Quality status

Possible tabs where supported:

Overview
Yield
Test
Quality
Genealogy
History

Quality hold must be unmistakable.

Held material must never visually resemble eligible inventory.

QE-004 and QE-011 should look like real quality-exception records.

Distinguish:

Observed facts

Signals/correlations

Hypotheses

Disposition / next action

Do not make site concentration look like proven root cause.

==================================================
12. IMPLEMENT STRATOS ERP
==================================================

Redesign Commercial ERP as:

STRATOS ERP
Commercial, Orders & Supply

Use SAP S/4HANA / Fiori as the strongest structural reference.

Suggested navigation where supported:

Home
Customers
Orders
Inventory
Supply
Commitments

ERP should feel business-object-centric.

Example order page:

ORD-1204
Helios AI

Header:
Order status
Requested quantity
Eligible supply
Gap
Requested date
Program

Then tabs/sections as supported:

Overview
Line Items
Supply
Allocations
Commitment History

Use realistic object-page composition:

header
summary facts
action area
line-item table
related records
history

For DR-009 make the quantity logic visually obvious:

1,000 Physical
↓
250 Held
150 Allocated
↓
600 Eligible

Demand
800

Gap
200

Keep these concepts separate:

Physical
Held
Allocated
Eligible
Committed

Do not collapse them into one "inventory" number.

==================================================
13. IMPLEMENT STRATOS PROGRAMOPS
==================================================

Redesign Program Planner as:

STRATOS PROGRAMOPS
Program Planning & Readiness

Suggested navigation where supported:

Portfolio
Programs
Milestones
Dependencies
Risks
Actions

The landing page should emphasize:

- programs
- next gates
- late/at-risk milestones
- actions
- dependencies

For PRG-A17 / Helios, use a visual program timeline if actual data supports it.

Example:

Architecture
────●────────

Validation
────────●────

Manufacturing
──────────●──

Customer acceptance
────────────●

Use actual source dates/status.

Program detail should prioritize:

Program
Overall state
Next milestone
Key risks
Open actions
Dependencies

Represent CR-017, QE-004 and DR-009 as program work/dependencies, not agent
telemetry.

This application should feel planning-oriented.

==================================================
14. CROSS-SYSTEM CONTINUITY
==================================================

Keep shared business objects recognizable across systems.

Examples:

PRG-A17

CR-017

CR-019

QE-004

QE-011

LOT-B-204

ORD-1204

Use stable IDs exactly as they exist.

Where a relationship already exists in the data, surface it visually.

Example:

PLM
CR-017
Program: PRG-A17

MES
LOT-B-204
Program: PRG-A17

ERP
ORD-1204
Program: PRG-A17

Do not add cross-system writes for cosmetic reasons.

==================================================
15. SOURCE OWNERSHIP
==================================================

The UI should reinforce authoritative ownership:

Stratos PLM:
requirements
configuration
engineering change records

Stratos TestOps:
validation jobs
test execution/result evidence

Stratos MES:
lot status
manufacturing state
yield
quality hold/disposition

Stratos ERP:
orders
demand
inventory allocation
commercial commitment

Stratos ProgramOps:
program milestones
tasks
dependencies
readiness planning

Do not visually duplicate an authoritative record in another app in a way that
suggests multiple systems own it.

==================================================
16. TABLE DESIGN
==================================================

Enterprise systems need tables.

Keep them, but improve them.

Use:

- useful column prioritization
- readable row density
- aligned numeric columns
- concise statuses
- sort/filter where already supported
- master/detail patterns
- sticky headers where helpful
- selection states
- contextual actions

Avoid:

- excessive columns
- paragraph-length cells
- status pills everywhere
- decorative icons in every column

==================================================
17. SEARCH AND FILTER
==================================================

Where existing functionality supports it, make search/filtering native to the
domain.

PLM:
change / requirement / configuration / document

TestOps:
job / sample / test plan / result

MES:
lot / exception / product

ERP:
order / customer / material

ProgramOps:
program / milestone / owner

Do not invent backend search capabilities.

==================================================
18. DETAIL PANELS AND MODALS
==================================================

Use contextual side panels or large modals for secondary detail where appropriate.

Examples:

document preview

requirement detail

test evidence

quality exception detail

allocation detail

milestone detail

Use progressive disclosure.

Do not require full-page navigation for every secondary object.

==================================================
19. MINIMUM WORDS
==================================================

Use the rule:

IF FIVE SENTENCES CAN BECOME ONE CLEAR VISUAL,
USE THE VISUAL.

ERP example:

Instead of:
"Physical inventory is 1,000 units. 250 units are held and 150 are allocated,
leaving 600 eligible."

Show:

1,000 Physical
   ↓
250 Held
150 Allocated
   ↓
600 Eligible

Demand 800
Gap 200

MES:

First-pass yield
80%

Baseline
96%

-16 pts

PLM:

REQ-042
↓
CFG-B-01
↓
CR-017
↓
Validation impact

==================================================
20. STATUS DESIGN
==================================================

Avoid colored-background status pills everywhere.

Prefer:

icon + concise status text

Examples:

● Running
✓ Complete
! Hold
○ Scheduled

Important states such as HOLD or failed execution may use stronger visual
treatment.

Status must remain understandable without color alone.

==================================================
21. TYPOGRAPHY / SPACING
==================================================

Use a modern readable typography hierarchy.

Prefer the existing system font stack.

Use:

strong page title
clear section title
readable body
compact metadata
tabular numerals where helpful

Use whitespace to create structure.

Do not make text tiny to create "enterprise density."

==================================================
22. ICONOGRAPHY
==================================================

Use existing icon libraries where possible.

Use domain-recognizable concepts:

PLM:
product
change
configuration
requirement
document

TestOps:
sample
test
procedure
resource
result

MES:
factory
lot
quality
yield
hold

ERP:
order
customer
inventory
supply
delivery

ProgramOps:
timeline
milestone
dependency
risk
action

Keep icon styling consistent.

==================================================
23. REALISTIC DATA DENSITY
==================================================

The systems should feel populated and operational.

Use existing synthetic data.

Where fixtures already contain multiple records, expose enough to make the app
feel credible.

Do NOT change golden-path business facts.

Do not add arbitrary data that could influence agents, policies, calculations,
or tests.

If purely cosmetic placeholder content is absolutely necessary, isolate it from
authoritative workflow data.

==================================================
24. SOURCE APPS MUST REMAIN SOURCE APPS
==================================================

Do not turn these systems into agent dashboards.

These should look like the applications engineers, planners, manufacturing,
quality, supply and commercial teams work in every day.

Agent actions may appear naturally as existing activity/audit entries where data
supports it.

The main Agent Workspace remains in the Stratos control plane.

==================================================
25. AUDIT / HISTORY
==================================================

Where current data supports it, show realistic audit context:

Updated by
Updated at
Revision
Status history
Source/origin
Related record

Do not fabricate audit trails.

==================================================
26. IMPLEMENT DIRECTLY
==================================================

Unlike a prior preview-only task, DO NOT stop after proposing concepts.

After the research/audit:

1. choose the strongest coherent design direction;
2. directly modify the five source-system frontend UIs;
3. preserve the existing functionality;
4. keep changes scoped primarily to frontend presentation;
5. run the app;
6. visually inspect every redesigned system;
7. fix obvious UX/layout regressions;
8. run automated regression tests.

You may create temporary prototypes during exploration, but they are not the end
deliverable.

The actual source applications should be updated.

==================================================
27. PRESERVE CURRENT ROUTES / DEMO LINKS
==================================================

Do not break:

- direct source-app URLs
- navigation from Stratos control plane
- evidence/source links
- Concierge navigation
- demo walkthrough links
- reset harness
- test selectors where reasonably avoidable

If DOM changes require selector updates in tests, update tests to reflect the new
UI without weakening what they verify.

==================================================
28. EXISTING CONNECTED USE CASES MUST REMAIN IDENTICAL
==================================================

Explicitly verify these paths:

CR-017

PLM:
change + requirement/configuration evidence

TestOps:
validation scheduling/results

ProgramOps:
milestones/schedule

CR-019

PLM:
standard request/procedure/config

TestOps:
VALOPS-A17 intake

QE-004

MES:
LOT-B-204
quality exception
HOLD
yield state

ProgramOps:
recovery planning

DR-009

ERP:
ORD-1204
demand/order

MES:
physical/held/eligible material

PLM/TestOps:
technical readiness

ProgramOps:
commitment milestone

QE-011

MES:
quality_exception_created

touchless/background workflow support

No source behavior may change.

==================================================
29. CROSS-SYSTEM REGRESSION
==================================================

Verify agents still see the exact expected data after the UI redesign.

At minimum confirm:

- source API responses unchanged;
- MCP tools unchanged;
- CR-017 source reads unchanged;
- CR-019 source reads/writes unchanged;
- QE-004 source reads unchanged;
- QE-011 source-event path unchanged;
- DR-009 calculations unchanged;
- RAG integration unaffected;
- readback verification unaffected.

==================================================
30. BROWSER VERIFICATION
==================================================

Run browser verification across all five systems.

At minimum inspect:

STRATOS PLM
- list/home
- CR-017
- CR-019

STRATOS TESTOPS
- overview/list
- validation job
- result/evidence state

STRATOS MES
- overview
- LOT-B-204
- QE-004
- QE-011

STRATOS ERP
- overview
- ORD-1204
- inventory/supply view

STRATOS PROGRAMOPS
- portfolio/program view
- PRG-A17
- milestone/dependency view

Check:

- overflow
- clipping
- typography
- hierarchy
- data correctness
- navigation
- modal/side-panel behavior
- responsive layout
- loading/error states
- console errors

==================================================
31. VIEWPORTS
==================================================

Optimize primarily for:

1440x900
1920x1080

Also verify reasonable usability at:

1280x800

Do not make this mobile-first at the expense of enterprise desktop usability.

==================================================
32. ACCESSIBILITY
==================================================

Maintain:

- contrast
- keyboard focus
- semantic labels
- readable sizing
- accessible status
- reduced motion
- color-independent critical states

Minimalism must not reduce usability.

==================================================
33. BEFORE / AFTER
==================================================

Capture screenshots showing:

BEFORE
and
AFTER

for representative views from all five source applications.

At minimum:

1. PLM landing + CR-017
2. TestOps landing + job
3. MES landing + QE-004/lot
4. ERP landing + ORD-1204
5. ProgramOps landing + PRG-A17

The purpose is to make the visual improvement obvious.

==================================================
34. TESTS
==================================================

Run all relevant tests after implementation.

Include:

- frontend unit/component tests
- source app tests
- API regression tests
- MCP tests
- workflow/source integration tests
- reset tests
- browser/E2E tests
- typecheck
- frontend build

Do not make paid model calls merely to validate styling.

If an existing test fails because it depends on previous visual copy/layout,
update it only if the underlying business behavior remains correctly tested.

Do not weaken assertions simply to get green tests.

==================================================
35. DO NOT TOUCH THE MAIN CONTROL PLANE DESIGN
==================================================

Keep this task scoped to the five source apps.

Do not redesign:

- main Overview
- main Agent Workspace
- main Decisions surface
- main Operations
- Stratos Concierge
- main navigation

unless a tiny link/display-label change is necessary to reflect the new source
application names.

Do not mix this effort with the separate control-plane redesign.

==================================================
36. IMPLEMENTATION JUDGMENT
==================================================

Use judgment rather than mechanically following every suggested layout.

The primary success criteria are:

- realistic domain representation
- visual clarity
- modern minimalist UX
- preservation of functionality
- demo credibility

If research shows a better structure than an example in this prompt, use it
provided you preserve all constraints.

==================================================
37. FINAL REPORT
==================================================

After implementation, report:

1. Real-world application references researched.
2. Design direction chosen.
3. Stratos PLM changes.
4. Stratos TestOps changes.
5. Stratos MES changes.
6. Stratos ERP changes.
7. Stratos ProgramOps changes.
8. Display-name changes.
9. Files/components changed.
10. Confirmation APIs/contracts were unchanged.
11. Confirmation agents/MCP/workflows were unchanged.
12. Before/after screenshots.
13. Tests run and exact results.
14. Browser verification results.
15. Any known visual limitations.
16. Any follow-up improvements worth considering.

==================================================
38. SUCCESS CRITERIA
==================================================

A reviewer should immediately understand:

Stratos PLM
= engineering lifecycle / change-control system

Stratos TestOps
= silicon validation / test-operations system

Stratos MES
= semiconductor manufacturing / quality / yield system

Stratos ERP
= customer-order / inventory / supply / commercial system

Stratos ProgramOps
= program / milestone / dependency planning system

The apps should feel like five real enterprise systems sitting underneath the
Stratos agentic control plane.

They should remain:

modern
minimal
credible
information-rich
visually distinct
fast to understand
easy to demo

while preserving all existing backend behavior and connected workflows.

Proceed through research, redesign, implementation, verification and reporting
without waiting for an additional approval step.