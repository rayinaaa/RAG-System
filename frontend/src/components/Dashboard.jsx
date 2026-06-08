import { Activity, Database, FileText, Gauge, MessageCircle, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { getHealth } from "../services/api";
import { formatMs } from "../utils/format";

function Metric({ icon: Icon, label, value, tone }) {
  return (
    <div className="rounded border border-line bg-white/95 p-3 shadow-sm transition hover:-translate-y-0.5 hover:shadow-soft">
      <div className="flex items-start gap-3">
        <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded ${tone}`}>
          <Icon size={16} />
        </div>
        <div className="min-w-0">
          <p className="text-xs text-gray-500">{label}</p>
          <p className="mt-0.5 text-lg font-semibold text-gray-950">{value}</p>
        </div>
      </div>
    </div>
  );
}

export function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await getHealth();
        if (active) {
          setMetrics(data.metrics);
          setError("");
        }
      } catch (err) {
        if (active) setError(err.message);
      }
    };
    load();
    const interval = window.setInterval(load, 4000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <aside className="flex h-full w-full shrink-0 flex-col border-l border-line bg-panel/95 xl:w-80">
      <div className="border-b border-line bg-white/88 px-4 py-4 backdrop-blur">
        <h2 className="text-lg font-semibold text-gray-950">Dashboard</h2>
        <p className="text-xs text-gray-500">Live retrieval and generation metrics.</p>
      </div>
      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin">
        {error ? <p className="mb-4 rounded border border-red-100 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
          <Metric icon={FileText} label="Total documents" value={metrics?.total_documents ?? 0} tone="bg-emerald-50 text-emerald-700" />
          <Metric icon={Database} label="Total chunks" value={metrics?.total_chunks ?? 0} tone="bg-blue-50 text-blue-700" />
          <Metric icon={Gauge} label="Avg retrieval" value={formatMs(metrics?.average_retrieval_time_ms)} tone="bg-amber-50 text-amber-700" />
          <Metric icon={Activity} label="Avg generation" value={formatMs(metrics?.average_generation_time_ms)} tone="bg-rose-50 text-rose-700" />
          <Metric icon={MessageCircle} label="Queries processed" value={metrics?.total_queries_processed ?? 0} tone="bg-gray-100 text-gray-800" />
          <Metric icon={ShieldCheck} label="Avg confidence" value={`${Math.round((metrics?.average_confidence ?? 0) * 100)}%`} tone="bg-emerald-50 text-emerald-700" />
          <Metric icon={ShieldCheck} label="Retrieval success" value={`${Math.round((metrics?.retrieval_success_rate ?? 0) * 100)}%`} tone="bg-indigo-50 text-indigo-700" />
        </div>
      </div>
    </aside>
  );
}
