import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { analyticsApi, usersApi, profileApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";
import { Trophy, Target, TrendingUp, AlertCircle, BellRing, Mailbox } from "lucide-react";
import { toast } from "sonner";

export default function ParentDashboard() {
  const { user, setUser } = useAuth();
  const [children, setChildren] = useState([]);
  const [activeChild, setActiveChild] = useState(null);
  const [stats, setStats] = useState(null);
  const [threshold, setThreshold] = useState(String(user?.alert_drop_threshold ?? 15));
  const [alertMode, setAlertMode] = useState(user?.alert_mode ?? "instant");

  const saveThreshold = async (v) => {
    setThreshold(v);
    try {
      const u = await profileApi.updateSettings({ alert_drop_threshold: Number(v) });
      setUser(u);
      toast.success(`Alert when a score drops ${v} points or more`);
    } catch {
      toast.error("Could not update alert threshold");
    }
  };

  const saveAlertMode = async (v) => {
    setAlertMode(v);
    try {
      const u = await profileApi.updateSettings({ alert_mode: v });
      setUser(u);
      toast.success(v === "weekly" ? "Switched to a calmer weekly summary" : "Instant drop alerts on");
    } catch {
      toast.error("Could not update alert preference");
    }
  };

  useEffect(() => {
    (async () => {
      if (!user.child_ids?.length) return;
      const cs = await Promise.all(user.child_ids.map(id => usersApi.get(id)));
      setChildren(cs);
      setActiveChild(cs[0]);
    })();
  }, [user]);

  useEffect(() => {
    if (activeChild) analyticsApi.parent(activeChild.id).then(setStats);
  }, [activeChild]);

  return (
    <div data-testid="parent-dashboard" className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Family view</div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">Hi {user.name.split(" ")[0]}</h1>
          <p className="text-muted-foreground mt-1">Watch your child's prep, spot weak subjects early.</p>
        </div>
        {children.length > 1 && (
          <Select value={activeChild?.id} onValueChange={(v) => setActiveChild(children.find(c => c.id === v))}>
            <SelectTrigger className="w-64"><SelectValue /></SelectTrigger>
            <SelectContent>{children.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
          </Select>
        )}
      </div>

      {!activeChild && (
        <Card className="en-card p-6 text-sm text-muted-foreground">
          No child linked to your account yet. Sign up with your child's registered email during account creation.
        </Card>
      )}

      {activeChild && (
        <>
          <Card data-testid="alert-threshold-card" className="en-card p-5">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-xl grid place-items-center bg-destructive/10 text-destructive shrink-0"><BellRing className="h-5 w-5" /></div>
                <div>
                  <div className="font-medium">Score-drop alerts</div>
                  <div className="text-sm text-muted-foreground">Email me when a mock score falls this much below the recent average.</div>
                </div>
              </div>
              <Select value={threshold} onValueChange={saveThreshold} disabled={alertMode === "weekly"}>
                <SelectTrigger data-testid="alert-threshold-select" className="w-36 rounded-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {[5, 10, 15, 20, 25, 30, 40].map((n) => <SelectItem key={n} value={String(n)}>{n} points</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-4 mt-5 pt-5 border-t border-border">
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-xl grid place-items-center bg-primary/10 text-primary shrink-0"><Mailbox className="h-5 w-5" /></div>
                <div>
                  <div className="font-medium">How should we alert you?</div>
                  <div className="text-sm text-muted-foreground">Instant emails on each big drop, or a calmer weekly-only summary.</div>
                </div>
              </div>
              <Select value={alertMode} onValueChange={saveAlertMode}>
                <SelectTrigger data-testid="alert-mode-select" className="w-44 rounded-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="instant">Instant drop alerts</SelectItem>
                  <SelectItem value="weekly">Weekly summary only</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </Card>

          <Card className="en-card p-6">
            <div className="flex flex-wrap items-center gap-6">
              <div className="flex items-center gap-4">
                <Avatar className="h-16 w-16"><AvatarImage src={activeChild.avatar} /><AvatarFallback>{activeChild.name?.[0]}</AvatarFallback></Avatar>
                <div>
                  <div className="font-display font-bold text-xl">{activeChild.name}</div>
                  <div className="text-sm text-muted-foreground">{activeChild.email}</div>
                  <Badge variant="secondary" className="rounded-full mt-1">{activeChild.exam_target || "JEE"}</Badge>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 flex-1 min-w-64">
                <MiniStat icon={Target} label="Accuracy" value={`${stats?.accuracy || 0}%`} />
                <MiniStat icon={TrendingUp} label="Attempts" value={stats?.attempts || 0} />
                <MiniStat icon={Trophy} label="Rank" value={`#${stats?.rank || "—"}`} />
              </div>
            </div>
          </Card>

          <div className="grid lg:grid-cols-3 gap-6">
            <Card className="en-card p-6 lg:col-span-2">
              <h3 className="font-display font-semibold text-lg mb-4">Score trend</h3>
              <div className="h-64">
                {stats?.trend?.length > 0 ? (
                  <ResponsiveContainer>
                    <LineChart data={stats.trend}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="date" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                      <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                      <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12 }} />
                      <Line type="monotone" dataKey="accuracy" stroke="hsl(var(--secondary))" strokeWidth={3} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : <div className="h-full grid place-items-center text-muted-foreground text-sm">No attempts yet.</div>}
              </div>
            </Card>

            <Card className="en-card p-6">
              <h3 className="font-display font-semibold text-lg mb-4">Weak subjects</h3>
              <div className="space-y-4">
                {Object.entries(stats?.subject_stats || {}).map(([s, st]) => {
                  const acc = Math.round((st.correct / Math.max(st.total, 1)) * 100);
                  return (
                    <div key={s}>
                      <div className="flex justify-between text-sm">
                        <span className="flex items-center gap-2">{s} {acc < 50 && <AlertCircle className="h-3.5 w-3.5 text-destructive" />}</span>
                        <span className="font-medium">{acc}%</span>
                      </div>
                      <Progress value={acc} className="mt-1" />
                    </div>
                  );
                })}
                {(!stats?.subject_stats || Object.keys(stats.subject_stats).length === 0) && <div className="text-sm text-muted-foreground">No data yet.</div>}
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function MiniStat({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-3">
      <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary grid place-items-center"><Icon className="h-5 w-5" /></div>
      <div>
        <div className="text-xs text-muted-foreground uppercase tracking-wider">{label}</div>
        <div className="font-display font-bold text-xl">{value}</div>
      </div>
    </div>
  );
}
