import { ServiceWorkspace } from "@/components/part2b/service-workspace";

export default function Page() {
  return (
    <ServiceWorkspace
      title="Approvals"
      resources={["approvals"]}
      actions={["approve","reject","request-changes","delegate"]}
    />
  );
}