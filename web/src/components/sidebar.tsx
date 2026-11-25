"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AppIcon, type IconName } from "@/components/app-icon";
import { navigation } from "@/lib/navigation";

export function Sidebar() {
  const path = usePathname();
  const groups = [...new Set(navigation.map((item) => item.group))];

  return (
    <aside className="sidebar">
      <div className="brand"><div className="brandmark">F</div><span>FlowForge</span></div>
      <div className="company"><small>Company</small><strong>Apex Manufacturing</strong></div>
      {groups.map((group) => <div key={group}>
        <div className="navgroup">{group}</div>
        {navigation.filter((item) => item.group === group).map((item) => (
          <Link className={`navitem ${path === item.href ? "active" : ""}`} href={item.href} key={item.href}>
            <span className="navicon"><AppIcon name={item.icon as IconName} /></span>
            <span>{item.label}</span>
            {item.badge && <span className="badge">{item.badge}</span>}
          </Link>
        ))}
      </div>)}
    </aside>
  );
}