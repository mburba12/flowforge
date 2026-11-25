"use client";

import { DashboardActions } from "@/components/dashboard-actions";
import { MetricCard } from "@/components/metric-card";
import { StatusBanner } from "@/components/status-banner";
import { activities, workItems } from "@/lib/demo-data";

import { CashFlowChart } from "@/components/cash-flow-chart";
const metrics = [
  { label: "Available cash", value: "$1.27M", delta: "+4.8% this month", trend: "up" as const, tone: "positive" as const },
  { label: "Receivables", value: "$412.9k", delta: "$74.3k overdue", trend: "down" as const, tone: "warning" as const },
  { label: "Payables", value: "$184.3k", delta: "$62.4k due this week", trend: "up" as const, tone: "neutral" as const },
  { label: "Open work", value: "22", delta: "3 critical", trend: "up" as const, tone: "danger" as const },
];

export default function Dashboard() {
  return (
    <>
      <div className="pagehead">
        <div>
          <div className="eyebrow">Tuesday, November 24</div>
          <h1>Good evening, Mack</h1>
          <p>Here is what needs attention across Apex Manufacturing.</p>
        </div>
        <div className="actions dashboard-head-actions">
          <StatusBanner />
          <DashboardActions />
        </div>
      </div>

      <div className="metrics">{metrics.map((metric) => <MetricCard metric={metric} key={metric.label} />)}</div>

      <div className="grid">
        <section className="panel">
          <div className="panelhead"><h2>Cash flow outlook</h2><button className="btn" type="button">Last 30 days</button></div>
          <div className="panelbody"><CashFlowChart /></div>
        </section>
        <section className="panel">
          <div className="panelhead"><h2>Recent activity</h2><button className="btn" type="button">View all</button></div>
          <div className="panelbody">{activities.map((activity) => <div className="activity" key={activity.id}><span className="dot"/><div><strong>{activity.title}</strong><p>{activity.detail}</p><p>{activity.module} - {activity.timestamp}</p></div></div>)}</div>
        </section>
      </div>

      <div style={{ height: 18 }} />
      <div className="split">
        <section className="panel">
          <div className="panelhead"><h2>Priority work</h2><button className="btn" type="button">Open work queue</button></div>
          <div className="panelbody">{workItems.map((item) => <div className="workitem" key={item.id}><div className="worktop"><h3><span className={`severity ${item.severity}`}/>{item.title}</h3><span className="status">{item.status}</span></div><div className="workmeta">{item.module} - {item.owner} - Due {item.due}</div></div>)}</div>
        </section>
        <section className="panel">
          <div className="panelhead"><h2>Business health</h2></div>
          <div className="panelbody">
            <div className="featurecard"><h3>Order fulfillment</h3><p><strong className="positive">96.2%</strong> on time, up 1.4% from last month.</p></div>
            <div style={{ height: 9 }} /><div className="featurecard"><h3>Reconciliation</h3><p><strong className="warning">5 exceptions</strong> across cash, payroll, and inventory.</p></div>
            <div style={{ height: 9 }} /><div className="featurecard"><h3>Data freshness</h3><p>All critical sources synced within the last 18 minutes.</p></div>
          </div>
        </section>
      </div>
    </>
  );
}
