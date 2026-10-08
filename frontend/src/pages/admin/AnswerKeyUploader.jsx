import { useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { KeyRound, Sparkles, CheckCircle2 } from "lucide-react";

const SUBJECTS = ["Physics", "Chemistry", "Biology", "Mathematics"];

export default function AnswerKeyUploader({ onDone }) {
  const [keyText, setKeyText] = useState("");
  const [subject, setSubject] = useState("Physics");
  const [chapter, setChapter] = useState("");
  const [overwrite, setOverwrite] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const apply = async () => {
    if (keyText.trim().length < 4) { toast.error("Paste at least one entry like '1) 2'."); return; }
    setBusy(true);
    try {
      const r = await api.post("/questions/apply-answer-key", {
        key_text: keyText,
        subject: subject || null,
        chapter: chapter || null,
        overwrite,
      });
      setResult(r.data);
      toast.success(`Updated ${r.data.updated} question(s) · skipped ${r.data.skipped}`);
      onDone?.(r.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not apply answer key");
    } finally { setBusy(false); }
  };

  return (
    <Card data-testid="answer-key-uploader" className="en-card p-6 lg:p-8">
      <div className="flex items-center gap-3">
        <div className="h-11 w-11 rounded-xl bg-accent/15 text-accent grid place-items-center"><KeyRound className="h-5 w-5" /></div>
        <div>
          <div className="font-display font-semibold text-lg">Paste an answer key</div>
          <div className="text-sm text-muted-foreground">Apply it to questions you already imported — the Nth entry marks the Nth question.</div>
        </div>
      </div>

      <div className="mt-6 grid md:grid-cols-2 gap-4">
        <div>
          <Label>Subject</Label>
          <Select value={subject} onValueChange={setSubject}>
            <SelectTrigger data-testid="ak-subject" className="rounded-full mt-1"><SelectValue /></SelectTrigger>
            <SelectContent>{SUBJECTS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
          </Select>
        </div>
        <div>
          <Label>Chapter (optional)</Label>
          <input data-testid="ak-chapter" value={chapter} onChange={(e) => setChapter(e.target.value)}
            placeholder="e.g. Optics — leave blank for whole subject"
            className="mt-1 flex h-10 w-full rounded-full border border-input bg-transparent px-4 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" />
        </div>
      </div>

      <div className="mt-4">
        <Label>Answer key text</Label>
        <Textarea data-testid="ak-text" value={keyText} onChange={(e) => setKeyText(e.target.value)} rows={8}
          className="mt-1 font-mono text-sm"
          placeholder={"1) 2   2) 4   3) 1   4) 3\n5) 2   6) 1   7) 4   8) 2\n…or one per line:\n1. A\n2. B\n3. C"} />
        <p className="text-xs text-muted-foreground mt-2">
          Accepts <b>1) 2</b>, <b>1. B</b>, or <b>1: A</b> — number then letter (A/B/C/D) or option index (1/2/3/4).
        </p>
      </div>

      <label className="mt-4 flex items-center gap-2 cursor-pointer text-sm">
        <Checkbox data-testid="ak-overwrite" checked={overwrite} onCheckedChange={(v) => setOverwrite(!!v)} />
        Overwrite existing correct answers (default: skip questions that already have an answer)
      </label>

      <div className="mt-6 flex items-center justify-between flex-wrap gap-3">
        <div className="text-xs text-muted-foreground flex items-center gap-2">
          <Sparkles className="h-3.5 w-3.5" /> Matches keys to questions in the order they were imported (oldest first).
        </div>
        <Button data-testid="ak-apply" onClick={apply} disabled={busy} className="rounded-full">
          {busy ? "Applying…" : "Apply answer key"}
        </Button>
      </div>

      {result && (
        <div data-testid="ak-result" className="mt-6 p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10">
          <div className="flex items-center gap-2 font-semibold text-emerald-700 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4" /> Applied {result.updated} · skipped {result.skipped}
          </div>
          <div className="mt-3 text-xs text-muted-foreground grid grid-cols-2 sm:grid-cols-3 gap-2">
            <div>Parsed entries: <b className="text-foreground">{result.parsed_entries}</b></div>
            <div>Matched questions: <b className="text-foreground">{result.matched_questions}</b></div>
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {Object.entries(result.map_preview || {}).slice(0, 12).map(([n, l]) => (
              <Badge key={n} variant="secondary" className="rounded-full text-xs">Q{n} → {l}</Badge>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
