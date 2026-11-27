import { ServiceWorkspace } from "@/components/part2b/service-workspace";

export default function Page() {
  return (
    <ServiceWorkspace
      title="Administration"
      resources={["users","roles","permissions"]}
      actions={["activate","deactivate"]}
    />
  );
}