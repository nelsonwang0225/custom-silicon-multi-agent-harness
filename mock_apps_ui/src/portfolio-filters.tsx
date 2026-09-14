import { useState } from "react";
import { Link } from "react-router-dom";
import { useData } from "./data";

export function usePortfolioFilter() {
  const { data } = useData();
  const [customer, setCustomer] = useState("all");
  const [program, setProgram] = useState("all");
  const programs = data?.programs || [];
  const customers = [
    ...new Map(programs.map((p) => [p.customer_id, p.customer_name])).entries(),
  ];
  const matches = (id: string) =>
    (program === "all" || program === id) &&
    (customer === "all" ||
      programs.find((p) => p.id === id)?.customer_id === customer);
  const text = (id: string) => {
    const p = programs.find((p) => p.id === id);
    return `${id} ${p?.name || ""} ${p?.customer_name || ""} ${p?.product_id || ""} ${p?.owner || ""}`;
  };
  const controls = (
    <>
      <select
        aria-label="Customer filter"
        value={customer}
        onChange={(e) => {
          setCustomer(e.target.value);
          setProgram("all");
        }}
      >
        <option value="all">All customers</option>
        {customers.map(([id, name]) => (
          <option key={id} value={id}>
            {name}
          </option>
        ))}
      </select>
      <select
        aria-label="Program filter"
        value={program}
        onChange={(e) => setProgram(e.target.value)}
      >
        <option value="all">All programs</option>
        {programs
          .filter((p) => customer === "all" || p.customer_id === customer)
          .map((p) => (
            <option key={p.id} value={p.id}>
              {p.name || p.id}
            </option>
          ))}
      </select>
    </>
  );
  return { matches, controls, text, key: customer + ":" + program };
}
export function ProgramCell({ id }: { id: string }) {
  const { data } = useData();
  const p = data?.programs.find((p) => p.id === id);
  return (
    <div className="program-cell">
      <strong>{p?.customer_name || id}</strong>
      <Link className="cell-secondary" to={"/programs/" + id}>
        {p?.name || id}
      </Link>
      <small>{id}</small>
    </div>
  );
}
