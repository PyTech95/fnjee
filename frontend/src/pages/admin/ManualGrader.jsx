import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { CheckCircle2, Award, Image as ImageIcon, MessageSquare, Clock, User as UserIcon } from "lucide-react";

const RUBRIC_PRESETS = [
  { pct: 100, label: "Full credit", detail: "All steps correct, clean working" },
  { pct: 75,  label: "Mostly right", detail: "Minor error, method is sound" },
  { pct: 50,  label: "Half credit", detail: "Right idea, missing steps or wrong final" },
  { pct: 25,  label: "Partial",     detail: "Started well, incomplete" },
  { pct: 0,   label: "No credit",   detail: "Wrong or blank" },
];

export default function ManualGrader() {
  const [queue, setQueue] = useState([]);
  const [selected, setSelected] = useState(null);
  const [marks, setMarks] = useState(0);
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState(false);

  useEffect(() => { load(); }, []);
  const load = () => api.get("/grading/pending").then((r) => setQueue(r.data));

  const pick = (item) => {
    setSelected(item);
    setMarks(item.marks_awarded || 0);
    setComment(item.grader_comment || "");
  };

  const save = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      const r = await api.post(`/grading/${selected.attempt_id}/${selected.question_id}`, { marks, comment });
      toast.success(`Saved ${r.data.marks_awarded}/${selected.question_marks} marks`);
      setQueue((prev) => prev.filter((x) => !(x.attempt_id === selected.attempt_id && x.question_id === selected.question_id)));
      setSelected(null); setMarks(0); setComment("");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Save failed");
    } finally { setSaving(false); }
  };

  return (
    <div data-testid="manual-grader-page" className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Grading queue</div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">Manual grading · subjective answers</h1>
          <p className="text-muted-foreground mt-1">Notebook photos and typed subjective answers awaiting review.</p>
        </div>
        <Badge variant="secondary" className="rounded-full">{queue.length} pending</Badge>
      </div>

      <div className="grid lg:grid-cols-[340px,1fr] gap-6">
        <Card className="en-card p-3 h-fit max-h-[80vh] overflow-y-auto en-scroll">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground px-2 py-2">Queue</div>
          <div className="space-y-1">
            {queue.length === 0 && <div data-testid="grader-empty" className="p-6 text-center text-sm text-muted-foreground">All caught up 🎉<br />No subjective answers pending grading.</div>}
            {queue.map((q) => {
              const active = selected && selected.attempt_id === q.attempt_id && selected.question_id === q.question_id;
              return (
                <button key={`${q.attempt_id}-${q.question_id}`}
                  data-testid={`grader-queue-item-${q.attempt_id.slice(0,6)}-${q.question_id.slice(0,6)}`}
                  onClick={() => pick(q)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors duration-200 ${
                    active ? "bg-primary/10 text-primary" : "hover:bg-muted"
                  }`}>
                  <div className="flex items-start gap-2">
                    <UserIcon className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      <div className="font-semibold truncate">{q.student_name}</div>
                      <div className="text-xs text-muted-foreground truncate">{q.question_text.slice(0, 60)}…</div>
                      <div className="mt-1 flex items-center gap-1.5 flex-wrap">
                        <Badge variant="outline" className="rounded-full text-[10px] px-1.5">{q.question_subject}</Badge>
                        {q.image_answer && <Badge variant="secondary" className="rounded-full text-[10px] px-1.5"><ImageIcon className="h-2.5 w-2.5 mr-0.5" />Photo</Badge>}
                        <span className="text-[10px] text-muted-foreground">/{q.question_marks} marks</span>
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </Card>

        {selected ? (
          <Card data-testid="grader-panel" className="en-card p-6 lg:p-8">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="secondary" className="rounded-full">{selected.question_subject}</Badge>
                {selected.question_chapter && <Badge variant="outline" className="rounded-full">{selected.question_chapter}</Badge>}
                <span className="text-xs text-muted-foreground flex items-center gap-1"><Clock className="h-3 w-3" /> {selected.submitted_at?.slice(0, 16).replace("T", " ")}</span>
              </div>
              <div className="text-sm text-muted-foreground">Grading for <b className="text-foreground">{selected.student_name}</b></div>
            </div>

            <div className="mt-6">
              <div className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground mb-2">Question</div>
              <div className="text-base leading-relaxed">{selected.question_text}</div>
            </div>

            {selected.user_answer?.[0] && (
              <div className="mt-6">
                <div className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground mb-2">Typed answer</div>
                <div className="p-4 rounded-xl border border-border bg-muted/30 text-sm whitespace-pre-wrap">{selected.user_answer[0]}</div>
              </div>
            )}

            {selected.image_answer && (
              <div className="mt-6">
                <div className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground mb-2 flex items-center gap-2">
                  Notebook photo
                  <Button size="sm" variant="ghost" className="h-6 px-2 text-xs" onClick={() => setPreview(true)} data-testid="grader-image-fullscreen">Fullscreen</Button>
                </div>
                <img data-testid="grader-image" src={selected.image_answer} alt="student answer" className="max-h-96 rounded-xl border border-border object-contain cursor-zoom-in" onClick={() => setPreview(true)} />
              </div>
            )}

            <div className="mt-8 pt-6 border-t border-border">
              <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary mb-3">Rubric</div>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                {RUBRIC_PRESETS.map((p) => {
                  const val = Math.round((p.pct / 100) * selected.question_marks * 10) / 10;
                  const active = marks === val;
                  return (
                    <button key={p.pct} onClick={() => setMarks(val)}
                      data-testid={`rubric-${p.pct}`}
                      className={`p-3 rounded-xl border text-left transition-colors duration-200 ${
                        active ? "border-primary bg-primary/10" : "border-border hover:border-primary/40"
                      }`}>
                      <div className={`font-display font-bold text-lg ${active ? "text-primary" : ""}`}>{val}<span className="text-xs text-muted-foreground">/{selected.question_marks}</span></div>
                      <div className="text-xs font-semibold mt-0.5">{p.label}</div>
                      <div className="text-[10px] text-muted-foreground mt-0.5">{p.detail}</div>
                    </button>
                  );
                })}
              </div>

              <div className="mt-4 grid sm:grid-cols-[180px,1fr] gap-3">
                <div>
                  <label className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">Custom marks</label>
                  <Input data-testid="grader-marks-input" type="number" step="0.5" min={0} max={selected.question_marks}
                    value={marks} onChange={(e) => setMarks(Math.max(0, Math.min(selected.question_marks, +e.target.value || 0)))}
                    className="mt-1 rounded-full" />
                </div>
                <div>
                  <label className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground flex items-center gap-1.5"><MessageSquare className="h-3 w-3" /> Comment for the student</label>
                  <Textarea data-testid="grader-comment" value={comment} onChange={(e) => setComment(e.target.value)}
                    rows={3} className="mt-1" placeholder="Nice approach — remember to reduce the fraction in step 3." />
                </div>
              </div>

              <div className="mt-6 flex gap-2 justify-end">
                <Button variant="outline" className="rounded-full" onClick={() => setSelected(null)}>Skip for now</Button>
                <Button data-testid="grader-save" className="rounded-full" onClick={save} disabled={saving}>
                  <Award className="h-4 w-4 mr-2" /> {saving ? "Saving…" : `Save · award ${marks}`}
                </Button>
              </div>
            </div>
          </Card>
        ) : (
          <Card className="en-card p-10 grid place-items-center text-center">
            <div>
              <div className="h-14 w-14 rounded-2xl bg-primary/10 text-primary mx-auto grid place-items-center mb-4"><CheckCircle2 className="h-7 w-7" /></div>
              <div className="font-display font-semibold text-lg">Pick an answer from the queue</div>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">Select a pending item on the left to see the student's work and award marks.</p>
            </div>
          </Card>
        )}
      </div>

      {preview && selected?.image_answer && (
        <div onClick={() => setPreview(false)} className="fixed inset-0 z-50 bg-black/90 grid place-items-center p-8 cursor-zoom-out">
          <img src={selected.image_answer} alt="fullscreen" className="max-h-full max-w-full object-contain" />
        </div>
      )}
    </div>
  );
}
