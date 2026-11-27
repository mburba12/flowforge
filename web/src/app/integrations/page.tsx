import { ServiceWorkspace } from "@/components/part2b/service-workspace";

export default function Page() {
  return (
    <ServiceWorkspace
      title="Integrations"
      resources={["integration-connections","integration-sync-runs","webhook-deliveries"]}
      actions={["test","sync","retry","enable","disable"]}
    />
  );
}