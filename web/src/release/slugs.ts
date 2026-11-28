/** Module slugs that have a full release workspace (shared by server and client code). */
export const RELEASE_SLUGS = ["dashboard", "finance", "ap", "ar", "orders", "inventory", "payroll", "workforce", "tax", "settings", "audit"] as const;

export function hasReleaseWorkspace(slug: string): boolean {
  return (RELEASE_SLUGS as readonly string[]).includes(slug);
}
