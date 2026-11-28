import { BusinessWorkspace } from "@/components/business-workspace";
import { hasReleaseWorkspace } from "@/release/slugs";
import { ReleaseWorkspace } from "@/release/workspaces";

export default async function ModulePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  // Release-scope domains have full workspaces; other modules keep the read-only browser.
  if (hasReleaseWorkspace(slug)) return <ReleaseWorkspace slug={slug} />;
  return <BusinessWorkspace slug={slug} />;
}