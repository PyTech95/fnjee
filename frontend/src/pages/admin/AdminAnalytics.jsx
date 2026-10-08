import { useEffect, useState, useMemo } from "react";
import { analyticsApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, CartesianGrid, Tooltip } from "recharts";
import { Grid3x3, Info } from "lucide-react";

export default function AdminAnalytics() {
  const [data, setData] = useState(null);
  const [board, setBoard] = useState([]);
  const [heat, setHeat] = useState(null);
  const [subject, setSubject] = useState("all");

  useEffect(() => {
    analyticsApi.admin().then(setData);
    analyticsApi.leaderboard("coins").then(setBoard);
  }, []);

  useEffect(() => {
    analyticsApi.questionHeatmap(subject === "all" ? undefined : subject).then(setHeat).catch(() => {});
  }, [subject]);

  return (
    <div data-testid="admin-analytics-page" className="space-y-6">
      <div>
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Insights</div>
        <h1 className="font-display font-bold text-3xl tracking-tight mt-1">Analytics</h1>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card className="en-card p-6">
          <h3 className="font-display font-semibold text-lg mb-4">Subject performance</h3>
          <div className="h-72">
            <ResponsiveContainer>
              <BarChart data={data?.subject_avg || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="subject" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12 }} />
                <Bar dataKey="avg_score" fill="hsl(var(--secondary))" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="en-card p-6">
          <h3 className="font-display font-semibold text-lg mb-4">Leaderboard</h3>
          <div className="space-y-2">
            {board.map((b, i) => (
              <div key={b.user.id} className="flex items-center justify-between p-3 rounded-xl bg-muted/40">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg grid place-items-center bg-primary/10 text-primary font-display font-bold text-sm">#{i + 1}</div>
                  <div>
                    <div className="font-medium text-sm">{b.user.name}</div>
                    <div className="text-xs text-muted-foreground">{b.user.exam_target}</div>
                  </div>
                </div>
                <Badge variant="secondary" className="rounded-full">{b.count} pts</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <QuestionHeatmap heat={heat} subject={subject} setSubject={setSubject} />
    </div>
  );
}

const BAND = {
  easy: { bg: "bg-emerald-500", label: "Easy (≥75% correct)" },
  medium: { bg: "bg-amber-500", label: "Medium (45–74%)" },
  hard: { bg: "bg-rose-500", label: "Hard (<45%)" },
  unknown: { bg: "bg-slate-300 dark:bg-slate-600", label: "No data" },
};

function cellColor(acc, band) {
  if (band === "unknown") return "bg-slate-200 dark:bg-slate-700 text-slate-500";
  // green → red gradient by accuracy
  if (acc >= 85) return "bg-emerald-600 text-white";
  if (acc >= 70) return "bg-emerald-400 text-white";
  if (acc >= 55) return "bg-amber-400 text-amber-950";
  if (acc >= 40) return "bg-orange-500 text-white";
  return "bg-rose-600 text-white";
}

function QuestionHeatmap({ heat, subject, setSubject }) {
  const [hover, setHover] = useState(null);
  const subjects = heat?.subjects || [];
  const cells = heat?.cells || [];

  const grouped = useMemo(() => {
    const g = {};
    for (const c of cells) (g[c.subject] ||= []).push(c);
    return g;
  }, [cells]);

  return (
    <Card className="en-card p-6" data-testid="question-heatmap">
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <Grid3x3 className="h-4 w-4 text-primary" />
        <h3 className="font-display font-semibold text-lg">Question difficulty heatmap</h3>
        <span className="text-xs text-muted-foreground">observed from {heat?.total_questions ?? 0} answered questions across all attempts</span>
        <div className="ml-auto flex flex-wrap gap-1.5">
          <Button size="sm" variant={subject === "all" ? "default" : "outline"} className="rounded-full h-7 px-3 text-xs" onClick={() => setSubject("all")}>All</Button>
          {subjects.map((s) => (
            <Button key={s} size="sm" variant={subject === s ? "default" : "outline"} className="rounded-full h-7 px-3 text-xs" onClick={() => setSubject(s)}>{s}</Button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-4 text-xs text-muted-foreground">
        {Object.values(BAND).map((b) => (
          <span key={b.label} className="flex items-center gap-1.5"><span className={`h-3 w-3 rounded ${b.bg}`} />{b.label}</span>
        ))}
      </div>

      {cells.length === 0 ? (
        <div className="text-sm text-muted-foreground py-12 text-center flex flex-col items-center gap-2" data-testid="heatmap-empty">
          <Info className="h-6 w-6" />
          No attempt data yet. Once students submit tests, per-question difficulty appears here.
        </div>
      ) : (
        <div className="space-y-5">
          {Object.entries(grouped).map(([subj, list]) => (
            <div key={subj}>
              <div className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">{subj} · {list.length} Q</div>
              <div className="flex flex-wrap gap-1.5">
                {list.map((c) => (
                  <div
                    key={c.question_id}
                    data-testid={`heat-cell-${c.question_id}`}
                    onMouseEnter={() => setHover(c)}
                    onMouseLeave={() => setHover(null)}
                    className={`h-9 w-9 rounded-md grid place-items-center text-[10px] font-bold cursor-default transition-transform hover:scale-110 tabular-nums ${cellColor(c.accuracy, c.observed_difficulty)}`}
                    title={`${c.accuracy}% correct · ${c.seen} attempts`}
                  >
                    {c.observed_difficulty === "unknown" ? "–" : `${Math.round(c.accuracy)}`}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {hover && (
        <div className="mt-4 p-3 rounded-xl bg-muted/50 border border-border text-sm" data-testid="heatmap-detail">
          <div className="font-medium mb-1">{hover.chapter}{hover.topic ? ` · ${hover.topic}` : ""}</div>
          <div className="text-muted-foreground">{hover.text}</div>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <Badge variant="outline" className="rounded-full">{hover.accuracy}% accuracy</Badge>
            <Badge variant="outline" className="rounded-full">{hover.seen} attempts</Badge>
            <Badge variant="outline" className="rounded-full text-emerald-600">{hover.correct} correct</Badge>
            <Badge variant="outline" className="rounded-full text-rose-600">{hover.wrong} wrong</Badge>
            <Badge variant="secondary" className="rounded-full">tagged: {hover.tagged_difficulty}</Badge>
            <Badge className="rounded-full">observed: {hover.observed_difficulty}</Badge>
          </div>
        </div>
      )}
    </Card>
  );
}
