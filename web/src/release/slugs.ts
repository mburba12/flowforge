/** Module slugs that have a full release workspace (shared by server and client code). */
export const RELEASE_SLUGS = ["finance"] as const;

export function hasReleaseWorkspace(slug: string): boolean {
  return (RELEASE_SLUGS as readonly string[]).includes(slug);
}
