import { ServiceWorkspace } from "@/components/part2b/service-workspace";

export default function Page() {
  return (
    <ServiceWorkspace
      title="Support"
      resources={["support/cases"]}
      actions={["assign","resolve","reopen"]}
    />
  );
}