import { useEffect, useRef, useState } from "react";
import { aiTutorApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Bot, Sparkles, Send, History, Loader2 } from "lucide-react";
import { toast } from "sonner";
import MathText from "@/components/MathText";

const SUBJECTS = ["Auto-detect", "Physics", "Chemistry", "Biology", "Mathematics"];
const SAMPLES = [
  "A ball is thrown up at 20 m/s. Find the maximum height. (g = 10)",
  "Why is benzene more stable than expected? Explain aromaticity.",
  "Differentiate between mitosis and meiosis with key points.",
  "Solve: integral of x·e^x dx.",
];

export default function AiTutor() {
  const [question, setQuestion] = useState("");
  const [subject, setSubject] = useState("Auto-detect");
  const [busy, setBusy] = useState(false);
  const [current, setCurrent] = useState(null);
  const [history, setHistory] = useState([]);
  const answerRef = useRef(null);

  useEffect(() => { aiTutorApi.history().then(setHistory).catch(() => {}); }, []);

  const ask = async () => {
    const q = question.trim();
    if (q.length < 5) { toast.error("Type your doubt first"); return; }
    setBusy(true); setCurrent(null);
    try {
      const res = await aiTutorApi.solve({ question: q, subject: subject === "Auto-detect" ? null : subject });
      setCurrent(res);
      setHistory((h) => [res, ...h]);
      setTimeout(() => answerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "AI tutor could not answer. Try again.");
    } finally { setBusy(false); }
  };

  return (
    <div data-testid="ai-tutor-page" className="space-y-6 max-w-4xl">
      <div>
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary flex items-center gap-2">
          <Bot className="h-3.5 w-3.5" /> AI Doubt Solver
        </div>
        <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">Ask your doubt, get a step-by-step answer</h1>
        <p className="text-muted-foreground mt-1">Physics, Chemistry, Biology & Maths — explained the way a topper would.</p>
      </div>

      <Card className="en-card p-6 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="w-full sm:w-56">
            <Select value={subject} onValueChange={setSubject}>
              <SelectTrigger data-testid="tutor-subject"><SelectValue /></SelectTrigger>
              <SelectContent>{SUBJECTS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
            </Select>
          </div>
        </div>
        <Textarea
          data-testid="tutor-question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) ask(); }}
          placeholder="Type or paste your question here…  (Ctrl/⌘ + Enter to ask)"
          className="min-h-[120px] resize-y"
        />
        <div className="flex flex-wrap items-center gap-2">
          {SAMPLES.map((s) => (
            <button key={s} data-testid="tutor-sample" onClick={() => setQuestion(s)}
              className="text-xs px-3 py-1.5 rounded-full border border-border hover:bg-muted transition-colors text-muted-foreground">
              {s.length > 42 ? s.slice(0, 42) + "…" : s}
            </button>
          ))}
        </div>
        <Button data-testid="tutor-ask" onClick={ask} disabled={busy} className="rounded-full">
          {busy ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Thinking…</> : <><Send className="h-4 w-4 mr-2" /> Ask the tutor</>}
        </Button>
      </Card>

      {current && (
        <Card ref={answerRef} data-testid="tutor-answer" className="en-card p-6 border-primary/30">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-8 w-8 rounded-xl bg-primary/10 text-primary grid place-items-center"><Sparkles className="h-4 w-4" /></div>
            <div className="font-display font-semibold">Solution</div>
            {current.subject && <Badge variant="secondary" className="rounded-full">{current.subject}</Badge>}
          </div>
          <Solution text={current.solution} />
        </Card>
      )}

      {history.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3 text-sm font-medium text-muted-foreground">
            <History className="h-4 w-4" /> Recent doubts
          </div>
          <div className="space-y-3">
            {history.slice(0, 8).map((h) => (
              <details key={h.id} data-testid={`tutor-history-${h.id}`} className="en-card p-4 group">
                <summary className="cursor-pointer text-sm font-medium list-none flex items-start gap-2">
                  <span className="text-primary">Q</span><span className="flex-1">{h.question}</span>
                </summary>
                <div className="mt-3 pt-3 border-t border-border"><Solution text={h.solution} /></div>
              </details>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Lightweight renderer: supports **bold** and inline/blocks LaTeX via MathText.
function Solution({ text }) {
  const lines = String(text || "").split("\n");
  return (
    <div className="space-y-1.5 text-sm leading-relaxed">
      {lines.map((line, i) => {
        if (!line.trim()) return <div key={i} className="h-2" />;
        const segs = line.split(/(\*\*[^*]+\*\*)/g);
        return (
          <div key={i}>
            {segs.map((seg, j) => {
              if (seg.startsWith("**") && seg.endsWith("**")) {
                return <strong key={j} className="text-foreground"><MathText>{seg.slice(2, -2)}</MathText></strong>;
              }
              return <MathText key={j}>{seg}</MathText>;
            })}
          </div>
        );
      })}
    </div>
  );
}
