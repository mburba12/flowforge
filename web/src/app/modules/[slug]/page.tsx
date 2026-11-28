import { BusinessWorkspace } from "@/components/business-workspace";
import { hasExtendedWorkspace, hasReleaseWorkspace } from "@/release/slugs";
import { ReleaseWorkspace } from "@/release/workspaces";
import { ExtendedWorkspace, OperationsSection } from "@/release/workspaces/extended";

export default async function ModulePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  // Release domains have purpose-built workspaces; extended domains are generated from the
  // operation catalog; the rest keep the record browser. Every operation stays reachable
  // (OperationsSection, folded away under "Advanced", or the extended console). Files and
  // the Upload button for every section live in the top bar (AppShell).
  if (hasReleaseWorkspace(slug))
    return (
      <>
        <ReleaseWorkspace slug={slug} />
        <OperationsSection slug={slug} />
      </>
    );
  if (hasExtendedWorkspace(slug)) return <ExtendedWorkspace slug={slug} />;
  return (
    <>
      <BusinessWorkspace slug={slug} />
      <OperationsSection slug={slug} />
    </>
  );
}
