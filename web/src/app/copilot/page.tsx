import { ServiceWorkspace } from "@/components/part2b/service-workspace";

export default function Page() {
  return (
    <ServiceWorkspace
      title="Copilot"
      resources={["copilot/conversations"]}
      actions={[]}
    />
  );
}