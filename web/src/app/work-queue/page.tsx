import { ServiceWorkspace } from "@/components/part2b/service-workspace";

export default function Page() {
  return (
    <ServiceWorkspace
      title="Work queue"
      resources={["work-items"]}
      actions={["assign","start","complete","reopen"]}
    />
  );
}