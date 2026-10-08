import { useState } from "react";
import { adaptiveApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Gauge, CheckCircle2, XCircle, TrendingUp, TrendingDown, Loader2, Zap, RotateCcw } from "lucide-react";
import MathText from "@/components/MathText";
import { QuestionContent, QuestionImage } from "@/components/QuestionContent";
import { toast } from "sonner";

const LETTERS = ["A", "B", "C", "D", "E", "F"];
const SUBJECTS = ["Physics", "Chemistry", "Biology", "Mathematics"];
const DIFF = { easy: { c: "text-emerald-600", b: "bg-emerald-500/10" }, medium: { c: "text-amber-600", b: "bg-amber-500/10" }, hard: { c: "text-rose-600", b: "bg-rose-500/10" } };

export default function Adaptive() {
  const [subject, setSubject] = useState("Physics");
  const [sess, setSess] = useState(null);
  const [q, setQ] = useState(null);
  const [meta, setMeta] = useState({ index: 0, length: 0, difficulty: "medium" });
  const [sel, setSel] = useState(null);
  const [result, setResult] = useState(null);
  const [summary, setSummary] = useState(null);
  const [busy, setBusy] = useState(false);

  const start = async () => {
    setBusy(true); setSummary(null);
    try {
      const res = await adaptiveApi.start({ subject, length: 12 });
      setSess(res.session_id); setQ(res.question); setSel(null); setResult(null);
      setMeta({ index: res.index, length: res.length, difficulty: res.difficulty });
    } catch (e) { toast.error(e?.response?.data?.detail || "Could not start"); } finally { setBusy(false); }
  };

  const answer = async () => {
    if (sel == null) return;
    setBusy(true);
    try {
      const res = await adaptiveApi.answer({ session_id: sess, question_id: q.id, selected: [LETTERS[sel]] });
      setResult(res);
      if (res.finished) setSummary(res.summary);
    } catch (e) { toast.error("Could not submit"); } finally { setBusy(false); }
  };

  const next = () => {
    if (result?.finished) return;
    setQ(result.question); setSel(null);
    setMeta((m) => ({ ...m, index: result.index, difficulty: result.next_difficulty }));
    setResult(null);
  };

  const d = DIFF[meta.difficulty] || DIFF.medium;

  return (
    <div data-testid="adaptive-page" className="space-y-6 max-w-3xl">
      <div>
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary flex items-center gap-2">
          <Gauge className="h-3.5 w-3.5" /> Adaptive CAT Mode
        </div>
        <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">Practice that fights back</h1>
        <p className="text-muted-foreground mt-1">Get one right and it gets harder. Slip up and it eases off — so you're always tested at your true level.</p>
      </div>

      {!sess && !summary && (
        <Card className="en-card p-6 space-y-4">
          <div>
            <div className="text-sm font-medium mb-2">Subject</div>
            <Select value={subject} onValueChange={setSubject}>
              <SelectTrigger data-testid="adaptive-subject" className="sm:w-64"><SelectValue /></SelectTrigger>
              <SelectContent>{SUBJECTS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <Button data-testid="adaptive-start" className="rounded-full" onClick={start} disabled={busy}>
            {busy ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Zap className="h-4 w-4 mr-2" />} Start adaptive session
          </Button>
        </Card>
      )}

      {sess && !summary && q && (
        <Card className="en-card p-6" data-testid="adaptive-card">
          <div className="flex items-center justify-between mb-4">
            <Badge className={`rounded-full border-0 ${d.b} ${d.c} capitalize`} data-testid="adaptive-difficulty">{meta.difficulty}</Badge>
            <span className="text-sm text-muted-foreground tabular-nums">Q{meta.index} / {meta.length}</span>
          </div>
          <div className="h-1.5 rounded-full bg-muted mb-5 overflow-hidden">
            <div className="h-full bg-primary transition-all" style={{ width: `${(meta.index / meta.length) * 100}%` }} />
          </div>
          <QuestionContent question={q} testId="adaptive-question" className="text-base font-medium leading-relaxed" />
          <div className="mt-4 space-y-2">
            {(q.options || []).map((opt, i) => {
              const isSel = sel === i;
              const isCorrect = result && result.correct_answer?.map((x) => x.toUpperCase()).includes(LETTERS[i]);
              const showWrong = result && isSel && !result.correct;
              return (
                <button key={i} data-testid={`adaptive-opt-${i}`} disabled={!!result} onClick={() => setSel(i)}
                  className={`w-full text-left p-3 rounded-xl border flex items-center gap-3 transition-colors ${
                    result ? (isCorrect ? "border-emerald-500 bg-emerald-500/10" : showWrong ? "border-rose-500 bg-rose-500/10" : "border-border opacity-70")
                    : isSel ? "border-primary bg-primary/10" : "border-border hover:bg-muted"}`}>
                  <span className={`h-6 w-6 rounded-full grid place-items-center text-xs font-bold shrink-0 ${isSel && !result ? "bg-primary text-primary-foreground" : "border border-border"}`}>{LETTERS[i]}</span>
                  <span className="flex-1"><MathText>{String(opt)}</MathText></span>
                  {result && isCorrect && <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
                  {showWrong && <XCircle className="h-4 w-4 text-rose-600" />}
                </button>
              );
            })}
          </div>

          {result && (
            <div className="mt-4 p-3 rounded-xl bg-muted/50 text-sm" data-testid="adaptive-feedback">
              <div className="flex items-center gap-2 font-semibold mb-1">
                {result.correct ? <><TrendingUp className="h-4 w-4 text-emerald-600" /> Correct — stepping up to <span className="capitalize">{result.next_difficulty}</span></>
                  : <><TrendingDown className="h-4 w-4 text-amber-600" /> Not quite — easing to <span className="capitalize">{result.next_difficulty}</span></>}
              </div>
              {result.explanation && <div className="text-muted-foreground"><MathText>{result.explanation}</MathText></div>}
              <QuestionImage src={result.explanation_image_url} alt="Solution illustration" testId="adaptive-solution-image" />
            </div>
          )}

          <div className="mt-5 flex justify-end">
            {!result ? (
              <Button data-testid="adaptive-submit" className="rounded-full" disabled={sel == null || busy} onClick={answer}>
                {busy ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null} Submit
              </Button>
            ) : (
              <Button data-testid="adaptive-next" className="rounded-full" onClick={next}>Next question</Button>
            )}
          </div>
        </Card>
      )}

      {summary && (
        <Card className="en-card p-8 text-center" data-testid="adaptive-summary">
          <div className="text-xs uppercase tracking-widest text-muted-foreground">Session complete</div>
          <div className="font-display font-bold text-5xl text-primary mt-2">{summary.ability}%</div>
          <div className="text-sm text-muted-foreground">ability score</div>
          <Badge className="rounded-full mt-3">{summary.band}</Badge>
          <div className="grid grid-cols-3 gap-4 mt-6 text-center">
            <div><div className="font-display font-bold text-xl">{summary.correct}/{summary.total}</div><div className="text-xs text-muted-foreground">correct</div></div>
            <div><div className="font-display font-bold text-xl">{summary.accuracy}%</div><div className="text-xs text-muted-foreground">accuracy</div></div>
            <div><div className="font-display font-bold text-xl capitalize">{summary.peak_difficulty}</div><div className="text-xs text-muted-foreground">peak level</div></div>
          </div>
          <Button className="rounded-full mt-6" onClick={() => { setSess(null); setQ(null); setSummary(null); }}>
            <RotateCcw className="h-4 w-4 mr-2" /> Another session
          </Button>
        </Card>
      )}
    </div>
  );
}
