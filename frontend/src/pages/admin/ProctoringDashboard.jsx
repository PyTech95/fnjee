import { useEffect, useState } from "react";
import { proctorApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ShieldAlert, ShieldCheck, ShieldX, RefreshCw } from "lucide-react";

const LABELS = {
  tab_switch: "Tab switch", fullscreen_exit: "Fullscreen exit", copy: "Copy",
  paste: "Paste", window_blur: "Window blur", idle: "Idle", right_click: "Right-click",
};

function trustBadge(score) {
  if (score >= 80) return { cls: "bg-emerald-500/10 text-emerald-600 border-emerald-500/30", Icon: ShieldCheck, label: "Low risk" };
  if (score >= 50) return { cls: "bg-amber-500/10 text-amber-600 border-amber-500/30", Icon: ShieldAlert, label: "Review" };
  return { cls: "bg-red-500/10 text-red-600 border-red-500/30", Icon: ShieldX, label: "High risk" };
}

export default function ProctoringDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = () => { setLoading(true); proctorApi.adminList().then(setData).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []);

  const rows = data?.rows || [];
  const flagged = rows.filter((r) => r.trust_score < 80).length;

  return (
    <div className="space-y-6" data-testid="proctoring-dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-semibold text-2xl">Exam Integrity</h1>
          <p className="text-sm text-muted-foreground mt-1">Attempts sorted by Trust Score — investigate the riskiest first.</p>
        </div>
        <button data-testid="proctor-refresh" onClick={load} className="inline-flex items-center gap-2 text-sm rounded-full border border-border px-4 py-2 hover:bg-muted transition-colors">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <Card className="en-card p-5"><div className="text-xs uppercase tracking-widest text-muted-foreground">Attempts</div><div className="font-display font-bold text-3xl mt-1">{rows.length}</div></Card>
        <Card className="en-card p-5"><div className="text-xs uppercase tracking-widest text-muted-foreground">Flagged (&lt;80)</div><div className="font-display font-bold text-3xl mt-1 text-amber-600">{flagged}</div></Card>
        <Card className="en-card p-5"><div className="text-xs uppercase tracking-widest text-muted-foreground">High risk (&lt;50)</div><div className="font-display font-bold text-3xl mt-1 text-red-600">{rows.filter((r) => r.trust_score < 50).length}</div></Card>
      </div>

      {data?.weights && (
        <Card className="en-card p-4">
          <div className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">Scoring weights (points deducted per event)</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(data.weights).map(([k, v]) => (
              <Badge key={k} variant="secondary" className="rounded-full">{LABELS[k] || k}: −{v}</Badge>
            ))}
          </div>
        </Card>
      )}

      <Card className="en-card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-muted-foreground">
              <tr>
                <th className="text-left p-3 font-semibold">Student</th>
                <th className="text-left p-3 font-semibold">Test</th>
                <th className="text-left p-3 font-semibold">Trust</th>
                <th className="text-left p-3 font-semibold">Violations</th>
                <th className="text-left p-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={5} className="p-6 text-center text-muted-foreground">Loading…</td></tr>}
              {!loading && rows.length === 0 && <tr><td colSpan={5} className="p-6 text-center text-muted-foreground">No attempts yet.</td></tr>}
              {rows.map((r) => {
                const b = trustBadge(r.trust_score);
                return (
                  <tr key={r.attempt_id} data-testid={`proctor-row-${r.attempt_id}`} className="border-t border-border hover:bg-muted/30">
                    <td className="p-3">
                      <div className="font-medium">{r.student}</div>
                      <div className="text-xs text-muted-foreground">{r.email}</div>
                    </td>
                    <td className="p-3">{r.test}</td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <span className="font-display font-bold text-lg">{r.trust_score}</span>
                        <Badge variant="outline" className={`rounded-full gap-1 ${b.cls}`}><b.Icon className="h-3 w-3" />{b.label}</Badge>
                      </div>
                    </td>
                    <td className="p-3">
                      {r.total_violations === 0 ? <span className="text-muted-foreground">—</span> : (
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(r.violation_counts).map(([k, v]) => (
                            <Badge key={k} variant="secondary" className="rounded-full text-xs">{LABELS[k] || k} ×{v}</Badge>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="p-3"><Badge variant="outline" className="rounded-full capitalize">{r.status?.replace("_", " ")}</Badge></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
