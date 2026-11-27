import { BusinessWorkspace } from "@/components/business-workspace";

export default async function ModulePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  return <BusinessWorkspace slug={slug} />;
}