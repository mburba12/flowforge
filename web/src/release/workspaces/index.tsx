"use client";

import { FinanceWorkspace } from "./finance";

const WORKSPACES: Record<string, () => React.JSX.Element> = {
  finance: FinanceWorkspace,
};


export function ReleaseWorkspace({ slug }: { slug: string }) {
  const Component = WORKSPACES[slug];
  return Component ? <Component /> : null;
}