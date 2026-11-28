import { redirect } from "next/navigation";

// Legacy route: the connected workspace lives under /modules.
export default function Page() {
  redirect("/modules/work-queue" as never);
}
