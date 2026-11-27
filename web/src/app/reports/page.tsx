import { ServiceWorkspace } from "@/components/part2b/service-workspace";

export default function Page() {
  return (
    <ServiceWorkspace
      title="Reports"
      resources={["reports","report-runs"]}
      actions={["run"]}
    />
  );
}