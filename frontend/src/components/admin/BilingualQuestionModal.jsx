import { useState } from "react";
import { questionsApi } from "@/lib/api";
import { toCbtQuestionShape, CbtQuestionView } from "@/components/exam/CbtQuestionView";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, Trash2, Eye } from "lucide-react";

const SUBJECTS = ["Physics", "Chemistry", "Mathematics", "Biology"];
const LETTERS = ["A", "B", "C", "D", "E", "F"];

const EMPTY = {
  type: "mcq_single", subject: "Physics", chapter: "", topic: "",
  difficulty: "medium", marks: 4, negative_marks: 1,
  text: "", text_hi: "", options: ["", "", "", ""], options_hi: ["", "", "", ""],
  correct: [], correct_numeric: "", section: "Section 1",
  nv: { integerOnly: false, allowDecimal: true, allowNegative: true, maxDecimalPlaces: 4, maxLength: 12 },
};

// Modal to create a bilingual CBT-ready question, with a live preview that
// uses the SAME renderer as the student exam.
export function BilingualQuestionModal({ open, onOpenChange, onCreated, defaultSubject }) {
  const [q, setQ] = useState({ ...EMPTY });
  const [busy, setBusy] = useState(false);
  const [previewLang, setPreviewLang] = useState("en");

  const upd = (k, v) => setQ((x) => ({ ...x, [k]: v }));
  const updNv = (k, v) => setQ((x) => ({ ...x, nv: { ...x.nv, [k]: v } }));
  const setOpt = (lang, i, v) => setQ((x) => {
    const key = lang === "hi" ? "options_hi" : "options";
    return { ...x, [key]: x[key].map((o, idx) => (idx === i ? v : o)) };
  });
  const addOpt = () => setQ((x) => ({ ...x, options: [...x.options, ""], options_hi: [...x.options_hi, ""] }));
  const removeOpt = (i) => setQ((x) => ({
    ...x,
    options: x.options.filter((_, idx) => idx !== i),
    options_hi: x.options_hi.filter((_, idx) => idx !== i),
    correct: x.correct.filter((l) => l !== LETTERS[i]),
  }));
  const toggleCorrect = (letter) => {
    if (q.type === "mcq_single" || q.type === "true_false") upd("correct", [letter]);
    else upd("correct", q.correct.includes(letter) ? q.correct.filter((l) => l !== letter) : [...q.correct, letter]);
  };

  const isNumerical = q.type === "integer" || q.type === "numerical";

  // Build a preview question in the CBT shape from current form state.
  const previewShape = toCbtQuestionShape({
    type: q.type, text: q.text, text_hi: q.text_hi,
    options: q.options.filter((o) => o !== ""), options_hi: q.options_hi,
    marks: q.marks, negative_marks: q.negative_marks,
    numerical_validation: isNumerical ? q.nv : null,
  });

  const submit = async (e) => {
    e.preventDefault();
    if (!q.text.trim()) return toast.error("English question text is required");
    if (!isNumerical && q.options.filter((o) => o.trim()).length < 2) return toast.error("Add at least 2 options");
    if (isNumerical && q.correct_numeric.trim() === "") return toast.error("Set the numerical correct answer");
    if (!isNumerical && q.correct.length === 0) return toast.error("Select the correct option(s)");
    setBusy(true);
    try {
      const payload = {
        type: isNumerical ? "integer" : q.type,
        subject: q.subject, chapter: q.chapter, topic: q.topic, difficulty: q.difficulty,
        marks: Number(q.marks), negative_marks: Number(q.negative_marks),
        text: q.text, text_hi: q.text_hi || "",
        options: isNumerical ? [] : q.options.filter((o) => o !== ""),
        options_hi: isNumerical ? [] : q.options.filter((o) => o !== "").map((_, i) => q.options_hi[i] || ""),
        correct: isNumerical ? [q.correct_numeric.trim()] : q.correct,
        explanation: "", hint: "", language: q.text_hi ? "Both" : "English", status: "approved",
        section: q.section || "Section 1",
        numerical_validation: isNumerical ? q.nv : null,
      };
      const created = await questionsApi.create(payload);
      toast.success("Question created");
      setQ({ ...EMPTY, subject: defaultSubject || "Physics" });
      onOpenChange(false);
      onCreated?.(created);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to create question");
    } finally { setBusy(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>New bilingual question</DialogTitle>
          <DialogDescription>Create a question with English and Hindi content and see a live preview.</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="grid lg:grid-cols-2 gap-6">
          {/* form */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Type</Label>
                <Select value={q.type} onValueChange={(v) => upd("type", v)}>
                  <SelectTrigger data-testid="bq-type"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="mcq_single">Single Correct</SelectItem>
                    <SelectItem value="mcq_multi">Multiple Correct</SelectItem>
                    <SelectItem value="integer">Numerical (Integer)</SelectItem>
                    <SelectItem value="numerical">Numerical (Decimal)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Subject</Label>
                <Select value={q.subject} onValueChange={(v) => upd("subject", v)}>
                  <SelectTrigger data-testid="bq-subject"><SelectValue /></SelectTrigger>
                  <SelectContent>{SUBJECTS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div><Label>Marks</Label><Input data-testid="bq-marks" type="number" value={q.marks} onChange={(e) => upd("marks", e.target.value)} /></div>
              <div><Label>Negative</Label><Input data-testid="bq-neg" type="number" step="0.5" value={q.negative_marks} onChange={(e) => upd("negative_marks", e.target.value)} /></div>
              <div>
                <Label>Difficulty</Label>
                <Select value={q.difficulty} onValueChange={(v) => upd("difficulty", v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="easy">Easy</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="hard">Hard</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div><Label>Question (English)</Label><Textarea data-testid="bq-text-en" rows={3} value={q.text} onChange={(e) => upd("text", e.target.value)} placeholder="Supports $math$ and tables" /></div>
            <div><Label>Question (Hindi)</Label><Textarea data-testid="bq-text-hi" rows={3} value={q.text_hi} onChange={(e) => upd("text_hi", e.target.value)} placeholder="हिंदी प्रश्न" /></div>

            {!isNumerical && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Options (EN / HI) — tick correct</Label>
                  <Button type="button" variant="ghost" size="sm" onClick={addOpt} data-testid="bq-add-opt"><Plus className="h-4 w-4" /></Button>
                </div>
                {q.options.map((opt, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <input type="checkbox" className="h-4 w-4 accent-green-600" checked={q.correct.includes(LETTERS[i])} onChange={() => toggleCorrect(LETTERS[i])} data-testid={`bq-correct-${LETTERS[i]}`} />
                    <span className="w-5 font-semibold text-slate-600">{LETTERS[i]}.</span>
                    <Input value={opt} onChange={(e) => setOpt("en", i, e.target.value)} placeholder="English" data-testid={`bq-opt-en-${LETTERS[i]}`} />
                    <Input value={q.options_hi[i]} onChange={(e) => setOpt("hi", i, e.target.value)} placeholder="हिंदी" data-testid={`bq-opt-hi-${LETTERS[i]}`} />
                    {q.options.length > 2 && (
                      <Button type="button" variant="ghost" size="sm" onClick={() => removeOpt(i)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {isNumerical && (
              <div className="space-y-3 rounded-lg border border-slate-200 p-3 bg-slate-50">
                <div><Label>Correct answer (number)</Label><Input data-testid="bq-correct-num" value={q.correct_numeric} onChange={(e) => upd("correct_numeric", e.target.value)} placeholder="e.g. 3.25" /></div>
                <div className="grid grid-cols-2 gap-3">
                  <label className="flex items-center justify-between text-sm"><span>Integer only</span><Switch checked={q.nv.integerOnly} onCheckedChange={(v) => updNv("integerOnly", v)} data-testid="bq-nv-int" /></label>
                  <label className="flex items-center justify-between text-sm"><span>Allow decimal</span><Switch checked={q.nv.allowDecimal} onCheckedChange={(v) => updNv("allowDecimal", v)} data-testid="bq-nv-dec" /></label>
                  <label className="flex items-center justify-between text-sm"><span>Allow negative</span><Switch checked={q.nv.allowNegative} onCheckedChange={(v) => updNv("allowNegative", v)} data-testid="bq-nv-neg" /></label>
                  <div><Label className="text-xs">Max decimals</Label><Input type="number" value={q.nv.maxDecimalPlaces} onChange={(e) => updNv("maxDecimalPlaces", parseInt(e.target.value || 0))} /></div>
                </div>
              </div>
            )}
          </div>

          {/* live preview */}
          <div className="lg:sticky lg:top-0 h-fit">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-700"><Eye className="h-4 w-4" /> Live preview</div>
              <div className="flex rounded overflow-hidden border border-slate-300 text-xs">
                <button type="button" onClick={() => setPreviewLang("en")} className={`px-2.5 py-1 ${previewLang === "en" ? "bg-[#0b2e59] text-white" : "bg-white"}`} data-testid="bq-prev-en">EN</button>
                <button type="button" onClick={() => setPreviewLang("hi")} className={`px-2.5 py-1 ${previewLang === "hi" ? "bg-[#0b2e59] text-white" : "bg-white"}`} data-testid="bq-prev-hi">हिं</button>
              </div>
            </div>
            <div className="rounded-lg border border-slate-300 bg-slate-100 p-4" data-testid="bq-preview">
              <div className="bg-white rounded border border-slate-200 p-4">
                <CbtQuestionView question={previewShape} lang={previewLang} readOnly showMeta />
              </div>
            </div>
            <Button type="submit" className="w-full mt-4 bg-green-600 hover:bg-green-700" disabled={busy} data-testid="bq-save">
              {busy ? "Saving…" : "Create question"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
