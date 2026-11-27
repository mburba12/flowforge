import Link from "next/link";

export default function Page() {
  return (
    <main>
      <div className="pageTitle">
        <small>FlowForge</small>
        <h1>Business operating system</h1>
        <p>
          Open the connected dashboard to access the live backend
          modules.
        </p>
      </div>

      <Link
        className="primary"
        href={"/modules/dashboard" as never}
      >
        Open dashboard
      </Link>
    </main>
  );
}