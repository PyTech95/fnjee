import { useEffect, useState } from "react";
import { analyticsApi, announcementsApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Users, BookOpen, ListChecks, TrendingUp, Bell } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer, CartesianGrid, Tooltip, PieChart, Pie, Cell, Legend
} from "recharts";
import { Link } from "react-router-dom";
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const COLORS = ["hsl(var(--chart-1))", "hsl(var(--chart-2))", "hsl(var(--chart-3))", "hsl(var(--chart-4))", "hsl(var(--chart-5))"];

function Stat({ icon: Icon, label, value, hint, tint = "primary" }) {
  return (
    <Card data-testid={`stat-${label.toLowerCase()}`} className="en-card p-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-muted-foreground uppercase tracking-wider">{label}</div>
          <div className="font-display font-bold text-3xl mt-2">{value}</div>
          {hint && <div className="text-xs text-muted-foreground mt-1">{hint}</div>}
        </div>
        <div className={`h-11 w-11 rounded-xl grid place-items-center bg-${tint}/10 text-${tint}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </Card>
  );
}

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [annOpen, setAnnOpen] = useState(false);
  const [ann, setAnn] = useState({ title: "", body: "", audience: "all" });

  const load = () => analyticsApi.admin().then(setData).catch(() => setData({}));
  useEffect(() => { load(); }, []);

  const sendAnn = async () => {
    try {
      await announcementsApi.create(ann);
      toast.success("Announcement sent");
      setAnnOpen(false); setAnn({ title: "", body: "", audience: "all" });
    } catch { toast.error("Failed to send"); }
  };

  if (!data) return <div className="text-muted-foreground">Loading…</div>;

  return (
    <div data-testid="admin-dashboard" className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Overview</div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">Admin Dashboard</h1>
          <p className="text-muted-foreground mt-1">Everything happening in your FNJEE.com at a glance.</p>
        </div>
        <div className="flex gap-2">
          <Link to="/admin/import"><Button data-testid="quick-import" className="rounded-full">Import questions</Button></Link>
          <Dialog open={annOpen} onOpenChange={setAnnOpen}>
            <DialogTrigger asChild>
              <Button data-testid="announce-btn" variant="outline" className="rounded-full">
                <Bell className="h-4 w-4 mr-2" /> Announce
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>New announcement</DialogTitle></DialogHeader>
              <div className="space-y-3">
                <div><Label>Title</Label><Input value={ann.title} onChange={(e) => setAnn({...ann, title: e.target.value})} /></div>
                <div><Label>Body</Label><Textarea value={ann.body} onChange={(e) => setAnn({...ann, body: e.target.value})} /></div>
              </div>
              <DialogFooter>
                <Button data-testid="announce-send" onClick={sendAnn}>Send to everyone</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat icon={Users} label="Students" value={data.students || 0} tint="primary" />
        <Stat icon={Users} label="Parents" value={data.parents || 0} tint="secondary" />
        <Stat icon={BookOpen} label="Questions" value={data.questions || 0} tint="accent" />
        <Stat icon={ListChecks} label="Tests" value={data.tests || 0} tint="primary" />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="en-card p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display font-semibold text-lg">Average score by subject</h3>
            <Badge variant="secondary" className="rounded-full">{data.attempts} attempts</Badge>
          </div>
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={data.subject_avg || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="subject" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12 }} />
                <Bar dataKey="avg_score" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="en-card p-6">
          <h3 className="font-display font-semibold text-lg mb-4">Question mix</h3>
          <div className="h-64">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={(data.subject_avg || []).map((s) => ({ name: s.subject, value: s.attempts }))}
                     dataKey="value" innerRadius={50} outerRadius={90}>
                  {(data.subject_avg || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Legend />
                <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card className="en-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-5 w-5 text-accent" />
            <h3 className="font-display font-semibold text-lg">Top performers</h3>
          </div>
          <div className="space-y-3">
            {(data.top_performers || []).map((u, i) => (
              <div key={u.id} className="flex items-center justify-between p-3 rounded-xl bg-muted/40">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg grid place-items-center bg-primary/10 text-primary font-display font-bold text-sm">{i+1}</div>
                  <div>
                    <div className="font-medium text-sm">{u.name}</div>
                    <div className="text-xs text-muted-foreground">{u.exam_target || "JEE"}</div>
                  </div>
                </div>
                <Badge variant="secondary" className="rounded-full">{u.reward_coins} pts</Badge>
              </div>
            ))}
          </div>
        </Card>

        <Card className="en-card p-6">
          <h3 className="font-display font-semibold text-lg mb-4">Most missed questions</h3>
          <div className="space-y-3">
            {(data.top_missed || []).map((m, i) => (
              <div key={i} className="p-3 rounded-xl bg-muted/40">
                <div className="flex items-start justify-between gap-3">
                  <div className="text-sm line-clamp-2">{m.question?.text}</div>
                  <Badge className="rounded-full bg-destructive/10 text-destructive hover:bg-destructive/15 border-destructive/20 shrink-0">
                    {m.wrong_count} wrong
                  </Badge>
                </div>
                <div className="text-xs text-muted-foreground mt-1">{m.question?.subject} · {m.question?.chapter}</div>
              </div>
            ))}
            {(!data.top_missed || data.top_missed.length === 0) && (
              <div className="text-sm text-muted-foreground">No wrong answers logged yet.</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
