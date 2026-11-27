import { workspaces } from "@/modules/blueprint/workspaces";

export default function EnterprisePage() {
  return (
    <main>
      <h1>FlowForge Enterprise</h1>

      <nav aria-label="Enterprise workspaces">
        <ul>
          {workspaces.map((workspace) => (
            <li key={workspace.slug}>
              <a href={`/enterprise/${workspace.slug}`}>
                {workspace.title}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </main>
  );
}
