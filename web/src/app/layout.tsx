import "./globals.css";import {Sidebar} from "@/components/sidebar";import {Topbar} from "@/components/topbar";import {FlowForgeAI} from "@/components/flowforge-ai";import Link from "next/link";
import { ModuleActionController } from "@/components/module-action-controller";
export const metadata={title:"FlowForge",description:"Business operations platform"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><div className="shell"><Sidebar/><main className="main"><Topbar/><div className="content">{children}</div></main></div><nav className="mobilebar"><Link href="/dashboard">Home</Link><Link href="/work-queue">Work</Link><Link href="/copilot">Copilot</Link><Link href="/settings">Settings</Link></nav><FlowForgeAI/>
<ModuleActionController />
</body></html>}
