import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { testsApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Users, Trophy, TrendingDown, Gauge } from "lucide-react";
import MathText from "@/components/MathText";

function Stat({ icon: Icon, label, value }) {
  return (
    <Card className="en-card p-4">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary grid place-items-center"><Icon className="h-4 w-4" /></div>
        <div><div className="text-xl font-display font-bold leading-none">{value}</div><div className="text-xs text-muted-foreground mt-0.5">{label}</div></div>
      </div>
    </Card>
  );
}

const barColor = (pct) => pct >= 70 ? "bg-emerald-500" : pct >= 40 ? "bg-amber-500" : "bg-red-500";

export default function TeacherResults() {
  const [params, setParams] = useSearchParams();
  const [papers, setPapers] = useState([]);
  const [testId, setTestId] = useState(params.get("test") || "");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { testsApi.list().then((r) => { setPapers(r); if (!testId && r[0]) setTestId(r[0].id); }); /* eslint-disable-next-line */ }, []);

  useEffect(() => {
    if (!testId) return;
    setLoading(true);
    setParams({ test: testId });
    testsApi.questionAnalysis(testId).then(setData).catch(() => setData(null)).finally(() => setLoading(false));
    /* eslint-disable-next-line */
  }, [testId]);

  return (
    <div data-testid="teacher-results" className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Analytics</div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">Results</h1>
          <p className="text-muted-foreground mt-1">Question-wise performance across all students who attempted this paper.</p>
        </div>
        <Select value={testId} onValueChange={setTestId}>
          <SelectTrigger data-testid="results-paper-select" className="w-72"><SelectValue placeholder="Select a paper" /></SelectTrigger>
          <SelectContent>{papers.map((p) => <SelectItem key={p.id} value={p.id}>{p.title}</SelectItem>)}</SelectContent>
        </Select>
      </div>

      {loading && <div className="text-muted-foreground">Loading…</div>}
      {!loading && data && (
        <>
          <div className="grid sm:grid-cols-4 gap-4">
            <Stat icon={Users} label="Students" value={data.students} />
            <Stat icon={Gauge} label="Avg score" value={data.avg_score} />
            <Stat icon={Trophy} label="High score" value={data.high_score} />
            <Stat icon={TrendingDown} label="Low score" value={data.low_score} />
          </div>

          <Card className="en-card overflow-hidden">
            <Table>
              <TableHeader><TableRow>
                <TableHead className="w-10">#</TableHead><TableHead>Question</TableHead><TableHead>Subject</TableHead>
                <TableHead>Difficulty</TableHead><TableHead className="w-56">Correct %</TableHead><TableHead className="text-right">Attempted</TableHead>
              </TableRow></TableHeader>
              <TableBody>
                {data.questions.length === 0 && <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground py-8">No attempts on this paper yet.</TableCell></TableRow>}
                {data.questions.map((q, i) => (
                  <TableRow key={q.question_id} data-testid={`qa-row-${q.question_id}`}>
                    <TableCell className="text-muted-foreground">{i + 1}</TableCell>
                    <TableCell className="max-w-sm"><div className="line-clamp-2 text-sm"><MathText>{q.text}</MathText></div></TableCell>
                    <TableCell><Badge variant="secondary" className="rounded-full">{q.subject}</Badge></TableCell>
                    <TableCell className="capitalize text-sm">{q.difficulty}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="h-2 flex-1 rounded-full bg-muted overflow-hidden"><div className={`h-full ${barColor(q.correct_pct)}`} style={{ width: `${q.correct_pct}%` }} /></div>
                        <span className="text-xs font-medium w-10 text-right">{q.correct_pct}%</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right text-sm">{q.attempted}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </>
      )}
    </div>
  );
}
