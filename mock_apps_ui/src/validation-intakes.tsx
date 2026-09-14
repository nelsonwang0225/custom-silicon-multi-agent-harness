import "./source-testops.css";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { request, type Schema } from "./api";
import { Badge, Banner, Empty, Facts, Heading, Panel, Table, date } from "./ui";
export function ValidationIntakes() {
  const { intakeId } = useParams();
  const [items, setItems] = useState<Schema["ValidationIntake"][] | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setItems(null);
    setError("");
    const load = async () => {
      if (intakeId)
        return [
          await request<Schema["ValidationIntake"]>(
            `/validation/intakes/${encodeURIComponent(intakeId)}`,
            "reader",
          ),
        ];
      const definitions = await request<{ items: Schema["StandardRequest"][] }>(
        "/engineering/standard-changes",
        "reader",
      );
      const lists = await Promise.all(
        definitions.items.map((r) =>
          request<Schema["IntakeList"]>(
            `/validation/changes/${r.change_id}/intakes`,
            "reader",
          ),
        ),
      );
      return lists.flatMap((x) => x.items);
    };
    void load()
      .then((v) => {
        if (active) setItems(v);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [intakeId]);
  return (
    <>
      <Heading
        eyebrow="Stratos TestOps / Work intake"
        title="Validation Operations intake"
        action={
          intakeId ? (
            <Link className="button" to="/validation/intakes">
              All intakes
            </Link>
          ) : undefined
        }
      />
      <Banner>
        Package receipt only · Lab authorization, scheduling and testing are
        separate.
      </Banner>
      {error && <p role="alert">{error}</p>}
      {!items && !error && <Empty>Reading source intakes…</Empty>}
      {items?.length === 0 && <Empty>No standard packages received.</Empty>}
      {!intakeId && !!items?.length && (
        <Panel
          title="Received packages"
          aside={<span className="metadata">{items.length} records</span>}
        >
          <Table
            headers={[
              "Intake / change",
              "Configuration / procedure",
              "Owner / queue",
              "Received · UTC",
              "State",
            ]}
          >
            {items.map((i) => (
              <tr key={i.id}>
                <td>
                  <Link
                    className="strong-link"
                    to={"/validation/intakes/" + i.id}
                  >
                    {i.id}
                  </Link>
                  <span className="cell-secondary">
                    {i.change_id} · {i.program_id}
                  </span>
                </td>
                <td>
                  {i.package.configuration.configuration_id}
                  <span className="cell-secondary">
                    {i.package.procedure_id} · v
                    {i.package.procedure_content_version}
                  </span>
                </td>
                <td>
                  {i.downstream_owner}
                  <span className="cell-secondary">
                    {i.downstream_queue_id}
                  </span>
                </td>
                <td>{date(i.received_at)}</td>
                <td>
                  <Badge value="received" />
                  <span className="cell-secondary">Authorization pending</span>
                </td>
              </tr>
            ))}
          </Table>
        </Panel>
      )}
      {intakeId &&
        items?.map((i) => (
          <Panel title={i.id} key={i.id} aside={<Badge value="received" />}>
            <div className="testops-intake-state">
              Complete package received · No lab job or reservation created
            </div>
            <Facts
              items={[
                ["Program / change", `${i.program_id} / ${i.change_id}`],
                [
                  "Owner / queue",
                  `${i.downstream_owner} / ${i.downstream_queue_id}`,
                ],
                ["Intake", "Received"],
                ["Package", `${i.package.package_id} · Complete`],
                [
                  "Procedure",
                  `${i.package.procedure_id} · v${i.package.procedure_content_version}`,
                ],
                [
                  "Configuration",
                  `${i.package.configuration.configuration_id} · ${i.package.configuration.firmware} · ${i.package.configuration.runtime}`,
                ],
                [
                  "Historical evidence",
                  i.package.reusable_evidence_ids.join(", "),
                ],
                ["Received", date(i.received_at)],
                ["Lab authorization", "Pending · Separate"],
                ["Physical testing", "Not started"],
                ["Customer acceptance", "Pending"],
              ]}
            />
            <div className="testops-intake-detail">
              <h3>Required standard work</h3>
              <Table headers={["Work item", "Description"]}>
                {i.package.remaining_work.map((w) => (
                  <tr key={w.work_id}>
                    <td>{w.work_id}</td>
                    <td>{w.description}</td>
                  </tr>
                ))}
              </Table>
              <details>
                <summary>Exact received package</summary>
                <pre
                  style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}
                >
                  {JSON.stringify(i.package, null, 2)}
                </pre>
              </details>
              <Link to="/control/programs/PRG-A17/cases/CR-019">
                Open standard case and verification
              </Link>
            </div>
          </Panel>
        ))}
    </>
  );
}
