import { Link } from "react-router-dom";
import { useData } from "./data";
import { ProgramCell } from "./portfolio-filters";
import { Badge, date, Empty, Panel, Table } from "./ui";
export function LabPortfolio({
  matches,
  history = false,
  status = "all",
  lab = "all",
  search = "",
  configuration = "all",
}: {
  matches: (id: string) => boolean;
  history?: boolean;
  status?: string;
  lab?: string;
  search?: string;
  configuration?: string;
}) {
  const { data } = useData();
  if (!data) return null;
  const jobs = data.cases.flatMap((c) => c.jobs);
  const rows = history
    ? [...data.history, ...jobs.filter((j) => j.completion)]
    : jobs;
  const shown = rows.filter(
    (j) =>
      matches(j.program_id) &&
      (configuration === "all" || j.configuration_id === configuration) &&
      (status === "all" ||
        (history && "timing" in j && j.completion
          ? status === "completed"
          : j.status === status)) &&
      (lab === "all" || lab === j.lab_id) &&
      `${j.id} ${j.configuration_id} ${j.sample_id}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  return (
    <Panel
      title={
        history ? "Recorded lab execution history" : "Portfolio scheduled jobs"
      }
      aside={<span>{shown.length} jobs</span>}
    >
      <Table
        headers={[
          "Job / customer",
          "Configuration / sample",
          "Lab / timing",
          "State",
          "Evidence / next action",
        ]}
      >
        {shown.map((j) => (
          <tr key={j.id}>
            <td>
              <Link
                className="strong-link"
                to={
                  "/validation/" + ("timing" in j ? "jobs/" : "history/") + j.id
                }
              >
                {j.id}
              </Link>
              <ProgramCell id={j.program_id} />
            </td>
            <td>
              {j.configuration_id}
              <span className="cell-secondary">{j.sample_id}</span>
              <span className="cell-secondary">{j.procedure_id}</span>
            </td>
            <td>
              {j.lab_id}
              <span className="cell-secondary">
                {date(
                  "timing" in j
                    ? history && j.completion
                      ? j.completion.completed_at
                      : j.timing.lab_start_at
                    : j.completed_at,
                )}
              </span>
            </td>
            <td>
              <Badge
                value={
                  "timing" in j && j.completion ? "result available" : j.status
                }
              />
              {"timing" in j && j.completion && (
                <span className="cell-secondary">
                  Booking remains scheduled
                </span>
              )}
            </td>
            <td>
              {"timing" in j ? (
                <>
                  {j.completion && (
                    <Link to={"/validation/results/" + j.completion.result_id}>
                      Open result
                    </Link>
                  )}
                  {data.cases.some((c) =>
                    c.links.some((l) => l.job_id === j.id),
                  ) ? (
                    <span className="cell-secondary">
                      {j.completion
                        ? "Engineering review is separate"
                        : "Await execution and engineering review"}
                    </span>
                  ) : (
                    <Link
                      className="cell-secondary"
                      to={"/programs/" + j.program_id}
                    >
                      Link scheduled work in Planner
                    </Link>
                  )}
                </>
              ) : (
                <>
                  {j.result_ids.map((id) => (
                    <Link
                      className="cell-secondary"
                      key={id}
                      to={"/validation/results/" + id}
                    >
                      {id}
                    </Link>
                  ))}
                  <span className="cell-secondary">
                    Acceptance remains separate
                  </span>
                </>
              )}
            </td>
          </tr>
        ))}
      </Table>
      {!shown.length && <Empty>No jobs match these filters.</Empty>}
    </Panel>
  );
}
