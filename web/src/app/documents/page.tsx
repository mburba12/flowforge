import { ServiceWorkspace } from "@/components/part2b/service-workspace";

export default function Page() {
  return (
    <ServiceWorkspace
      title="Documents"
      resources={["documents"]}
      actions={["archive"]}
    />
  );
}