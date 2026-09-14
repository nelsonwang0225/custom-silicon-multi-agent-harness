import { Component, type ReactNode } from "react";

export class WorkspaceBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (!this.state.failed) return this.props.children;
    return <section role="alert" className="panel padded">
      <h2>This workspace could not load</h2>
      <p>Check the local services, then reload. Existing business state is retained.</p>
      <button onClick={() => window.location.reload()}>Reload workspace</button>{" "}
      <a href="/control/overview">Return to Overview</a>
    </section>;
  }
}
