import { redirect } from "next/navigation";

// Legacy route: tenant setup lives in Administration.
export default function Page() {
  redirect("/modules/settings" as never);
}
