import {
  Callout,
  Classes,
  H3,
  Navbar,
  NavbarGroup,
  NavbarHeading,
} from "@blueprintjs/core";
import "@blueprintjs/core/lib/css/blueprint.css";
import "@blueprintjs/icons/lib/css/blueprint-icons.css";

// ponytail: shell chrome only — planner/evaluator wiring is a later build
function App() {
  return (
    <div className={Classes.DARK} style={{ minHeight: "100vh" }}>
      <Navbar>
        <NavbarGroup>
          <NavbarHeading>lunar-eval</NavbarHeading>
        </NavbarGroup>
      </Navbar>
      <main style={{ padding: 16 }}>
        <H3>Site×time planner</H3>
        <Callout intent="primary" title="Desktop shell">
          Product UI runs here (Tauri + Blueprint). Evaluator compute stays on
          this machine; remote role is horizon masks only.
        </Callout>
      </main>
    </div>
  );
}

export default App;
