import { agentRoles } from "./agent-roles";
export { agentRoles } from "./agent-roles";
export { AgentWorkspace as AgentActivity } from "./agent-workspace";
import { SourceLink, Facts, StatusText } from "./ui";
import { Dialog } from "./dialog";
export function AgentDetails({
  role,
  scope,
  close,
}: {
  role: (typeof agentRoles)[number];
  scope: string;
  close: () => void;
}) {
  return (
    <Dialog
      title={role.name}
      close={close}
      closeLabel="Close agent details"
      footer={
        <SourceLink to="/control/workflows/requirement_change_analysis">
          Workflow scope
        </SourceLink>
      }
    >
      <div className="cp-agent-detail">
        <StatusText tone="agent">Role definition</StatusText>
        <h3>Responsibilities</h3>
        <p>{role.responsibility}</p>
        <Facts
          rows={[
            ["Context", scope],
            ["Read sources", role.sources],
            ["Runtime role", role.id],
            ["Activity", "Unavailable · No task or result is implied"],
          ]}
        />
        <h3>Read-only scope</h3>
        <p>
          Access stays within the authorized program and case. No agent can
          approve engineering work, author test results, change customer
          commitments or execute a business mutation.
        </p>
      </div>
    </Dialog>
  );
}
