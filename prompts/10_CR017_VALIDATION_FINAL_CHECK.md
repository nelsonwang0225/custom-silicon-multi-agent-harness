# CR-017 validation final check

The user approved the single interactive engineering chip preview and requested
its implementation in the source system as the final check before publishing
CR-017 test results. Use the diagram to inspect the original versus updated
requirement, the validation scope and the outcome represented by the demo.

Scope: Stratos TestOps only, in the existing CR-017 lab job completion panel.
Preserve existing endpoints, schemas, publication action, lab identity,
idempotency, approval boundaries, result readback and downstream behavior.
Do not add a second approval or automatic publication step. Other cases and the
main control plane are outside this change.

Adapt the approved draggable/zoomable conceptual chip with selectable context,
compute and I/O regions and Original / Updated / Changes controls. Read business
values from existing source records. The geometry is illustrative and does not
represent a physical silicon change. Before publication, label the passing
result as a simulated preview; the existing explicit lab action creates the
recorded result. Do not fabricate measured results or engineering acceptance.

Verify the targeted source UI and publication path with isolated deterministic
HTTP/browser tests; inspect desktop layouts. No paid models or working-demo
reset.
