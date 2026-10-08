import { useEffect, useState, useCallback, useRef } from "react";
import { errorsApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { AlertTriangle, Activity, ShieldCheck, Trash2, ChevronDown, ChevronRight, RefreshCw } from "lucide-react";

const POLL_MS = 8000;

export default function SystemErrors() {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState({});
  const [ago, setAgo] = useState(0);
  const last = useRef(Date.now());

  const load = useCallback(async () => {
    try {
      const res = await errorsApi.list(100);
      setData(res);
      last.current = Date.now();
      setAgo(0);
    } catch { /* ignore transient */ }
  }, []);

  useEffect(() => {
    load();
    const poll = setInterval(load, POLL_MS);
    const tick = setInterval(() => setAgo(Math.round((Date.now() - last.current) / 1000)), 1000);
    return () => { clearInterval(poll); clearInterval(tick); };
  }, [load]);

  const clear = async () => {
    try { const r = await errorsApi.clear(); toast.success(`Cleared ${r.cleared} entries`); load(); }
    catch { toast.error("Could not clear"); }
  };

  const errors = data?.errors || [];
  const healthy = (data?.last_24h ?? 0) === 0;

  return (
    <div data-testid="system-errors-page" className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary flex items-center gap-2">
            <Activity className="h-3.5 w-3.5" /> Error tracking
          </div>
          <h1 className="font-display font-bold text-3xl tracking-tight mt-1">System health</h1>
          <div className="mt-2 text-sm text-muted-foreground">Live capture of backend exceptions · synced {ago}s ago</div>
        </div>
        <div className="flex gap-2">
          <Button data-testid="refresh-errors" variant="outline" className="rounded-full" onClick={load}>
            <RefreshCw className="h-4 w-4 mr-2" /> Refresh
          </Button>
          <Button data-testid="clear-errors" variant="ghost" className="rounded-full text-destructive" onClick={clear} disabled={errors.length === 0}>
            <Trash2 className="h-4 w-4 mr-2" /> Clear
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Errors (24h)" value={data?.last_24h ?? "—"} icon={AlertTriangle} tint={healthy ? "text-emerald-600" : "text-destructive"} bg={healthy ? "bg-emerald-500/10" : "bg-destructive/10"} />
        <StatCard label="Total captured" value={data?.total ?? "—"} icon={Activity} tint="text-primary" bg="bg-primary/10" />
        <StatCard label="Status" value={healthy ? "All clear" : "Investigate"} icon={healthy ? ShieldCheck : AlertTriangle} tint={healthy ? "text-emerald-600" : "text-amber-600"} bg={healthy ? "bg-emerald-500/10" : "bg-amber-500/10"} />
      </div>

      <Card className="en-card p-4 sm:p-6">
        <h3 className="font-display font-semibold text-lg mb-4">Recent exceptions</h3>
        {errors.length === 0 ? (
          <div className="text-sm text-muted-foreground py-12 text-center flex flex-col items-center gap-2" data-testid="errors-empty">
            <ShieldCheck className="h-8 w-8 text-emerald-500" />
            No captured errors. Your backend is running clean.
          </div>
        ) : (
          <div className="space-y-2">
            {errors.map((e) => {
              const isOpen = open[e.id];
              return (
                <div key={e.id} className="rounded-xl border border-border overflow-hidden" data-testid={`error-row-${e.id}`}>
                  <button className="w-full flex items-center gap-3 p-3 text-left hover:bg-muted/50" onClick={() => setOpen((o) => ({ ...o, [e.id]: !o[e.id] }))}>
                    {isOpen ? <ChevronDown className="h-4 w-4 shrink-0" /> : <ChevronRight className="h-4 w-4 shrink-0" />}
                    <Badge variant="outline" className="rounded-full text-destructive shrink-0">{e.error_type}</Badge>
                    <Badge variant="secondary" className="rounded-full shrink-0">{e.method}</Badge>
                    <span className="font-mono text-xs truncate">{e.path}</span>
                    <span className="text-xs text-muted-foreground ml-auto shrink-0">{(e.ts || "").replace("T", " ").slice(0, 19)}</span>
                  </button>
                  {isOpen && (
                    <div className="p-3 border-t border-border bg-muted/30 space-y-2">
                      <div className="text-sm"><b>Message:</b> {e.message}</div>
                      {e.user_id && <div className="text-xs text-muted-foreground">User: {e.user_id}</div>}
                      <pre className="text-[11px] leading-relaxed bg-background border border-border rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">{e.traceback}</pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}

function StatCard({ label, value, icon: Icon, tint, bg }) {
  return (
    <Card className="en-card p-5">
      <div className="flex items-center gap-3">
        <div className={`h-11 w-11 rounded-xl grid place-items-center ${bg} ${tint}`}><Icon className="h-5 w-5" /></div>
        <div>
          <div className="text-xs text-muted-foreground uppercase tracking-widest">{label}</div>
          <div className={`font-display font-bold text-2xl ${tint}`}>{value}</div>
        </div>
      </div>
    </Card>
  );
}
