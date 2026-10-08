import { useEffect, useState } from "react";
import { questionsApi, testsApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { Wand2 } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function TestBuilder() {
  const [t, setT] = useState({
    title: "", exam_type: "full_mock", description: "",
    subjects: ["Physics"], duration_minutes: 60,
    negative_marking: true, shuffle_questions: true, shuffle_options: false, show_solutions_after: true,
    proctor_cutoff: 0, proctor_action: "flag",
    question_ids: [], sections: [],
  });
  const [bank, setBank] = useState([]);
  const [difficulty, setDifficulty] = useState("");
  const [count, setCount] = useState(10);
  const nav = useNavigate();

  useEffect(() => { questionsApi.list({ limit: 500 }).then(setBank); }, []);

  const upd = (k, v) => setT((x) => ({ ...x, [k]: v }));
  const toggleQ = (id) => upd("question_ids", t.question_ids.includes(id) ? t.question_ids.filter(x => x !== id) : [...t.question_ids, id]);

  const toggleSubject = (s) => upd("subjects", t.subjects.includes(s) ? t.subjects.filter(x => x !== s) : [...t.subjects, s]);

  const randomFill = async () => {
    try {
      const r = await testsApi.random({ subjects: t.subjects, difficulty, count });
      upd("question_ids", r.question_ids);
      toast.success(`Picked ${r.question_ids.length} random questions`);
    } catch { toast.error("Random pick failed"); }
  };

  const save = async () => {
    if (!t.title) return toast.error("Title required");
    if (!t.question_ids.length) return toast.error("Add at least one question");
    try {
      const test = await testsApi.create(t);
      toast.success(`Test "${test.title}" created`);
      nav("/admin/tests");
    } catch { toast.error("Save failed"); }
  };

  const filteredBank = bank.filter(q => t.subjects.length === 0 || t.subjects.includes(q.subject));

  return (
    <div data-testid="test-builder-page" className="grid lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Build</div>
          <h1 className="font-display font-bold text-3xl tracking-tight mt-1">New test</h1>
        </div>

        <Card className="en-card p-6 space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div><Label>Title</Label><Input data-testid="test-title" value={t.title} onChange={(e) => upd("title", e.target.value)} placeholder="JEE Full Mock #2" /></div>
            <div>
              <Label>Exam type</Label>
              <Select value={t.exam_type} onValueChange={(v) => upd("exam_type", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="full_mock">Full mock</SelectItem>
                  <SelectItem value="chapter_wise">Chapter-wise</SelectItem>
                  <SelectItem value="topic_wise">Topic-wise</SelectItem>
                  <SelectItem value="pyq">Previous year</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div><Label>Description</Label><Textarea rows={2} value={t.description} onChange={(e) => upd("description", e.target.value)} /></div>
          <div className="grid md:grid-cols-3 gap-4">
            <div><Label>Duration (min)</Label><Input data-testid="test-duration" type="number" value={t.duration_minutes} onChange={(e) => upd("duration_minutes", parseInt(e.target.value || 0))} /></div>
            <div className="flex items-center justify-between border border-border rounded-lg px-3 py-2 mt-6">
              <Label htmlFor="neg">Negative marking</Label>
              <Switch id="neg" checked={t.negative_marking} onCheckedChange={(v) => upd("negative_marking", v)} />
            </div>
            <div className="flex items-center justify-between border border-border rounded-lg px-3 py-2 mt-6">
              <Label htmlFor="shq">Shuffle questions</Label>
              <Switch id="shq" checked={t.shuffle_questions} onCheckedChange={(v) => upd("shuffle_questions", v)} />
            </div>
          </div>
          <div>
            <Label>Subjects</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {["Physics", "Chemistry", "Mathematics", "Biology"].map(s => (
                <Badge key={s} data-testid={`subj-${s}`} onClick={() => toggleSubject(s)}
                  className={`cursor-pointer rounded-full ${t.subjects.includes(s) ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"}`}>{s}</Badge>
              ))}
            </div>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <Label>Proctoring cutoff (Trust Score)</Label>
              <Select value={String(t.proctor_cutoff)} onValueChange={(v) => upd("proctor_cutoff", Number(v))}>
                <SelectTrigger data-testid="proctor-cutoff"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="0">Off</SelectItem>
                  <SelectItem value="50">Flag below 50</SelectItem>
                  <SelectItem value="60">Flag below 60</SelectItem>
                  <SelectItem value="70">Flag below 70</SelectItem>
                  <SelectItem value="80">Flag below 80</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>When cutoff is breached</Label>
              <Select value={t.proctor_action} onValueChange={(v) => upd("proctor_action", v)}>
                <SelectTrigger data-testid="proctor-action"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="flag">Flag for review</SelectItem>
                  <SelectItem value="auto_submit">Auto-submit attempt</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </Card>

        <Card className="en-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display font-semibold text-lg">Auto-pick questions</h3>
            <div className="flex items-center gap-2">
              <Select value={difficulty || "any"} onValueChange={(v) => setDifficulty(v === "any" ? "" : v)}>
                <SelectTrigger className="w-32"><SelectValue placeholder="Any difficulty" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">Any</SelectItem>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
              <Input type="number" value={count} onChange={(e) => setCount(parseInt(e.target.value || 0))} className="w-20" />
              <Button data-testid="auto-pick-btn" variant="outline" onClick={randomFill} className="rounded-full"><Wand2 className="h-4 w-4 mr-2" />Pick</Button>
            </div>
          </div>
          <div className="max-h-96 overflow-y-auto en-scroll space-y-2 border border-border rounded-xl p-3">
            {filteredBank.map(q => (
              <label key={q.id} className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer ${t.question_ids.includes(q.id) ? "bg-primary/10 border border-primary/30" : "hover:bg-muted/60 border border-transparent"}`}>
                <input data-testid={`pick-${q.id}`} type="checkbox" className="mt-1 h-4 w-4 accent-primary" checked={t.question_ids.includes(q.id)} onChange={() => toggleQ(q.id)} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm line-clamp-2">{q.text}</div>
                  <div className="flex flex-wrap gap-2 mt-1">
                    <Badge variant="secondary" className="rounded-full">{q.subject}</Badge>
                    <Badge variant="outline" className="rounded-full">{q.difficulty}</Badge>
                    <Badge variant="outline" className="rounded-full">{q.marks} mk</Badge>
                  </div>
                </div>
              </label>
            ))}
          </div>
        </Card>
      </div>

      <div className="lg:sticky lg:top-24 h-fit space-y-4">
        <Card className="en-card p-6">
          <h3 className="font-display font-semibold text-lg mb-2">Summary</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">Questions</span><span className="font-medium">{t.question_ids.length}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Duration</span><span className="font-medium">{t.duration_minutes} min</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Type</span><span className="font-medium capitalize">{t.exam_type.replace("_", " ")}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Negative</span><span className="font-medium">{t.negative_marking ? "Yes" : "No"}</span></div>
          </div>
          <Button data-testid="save-test-btn" className="w-full rounded-full mt-4" onClick={save}>Save test</Button>
        </Card>
      </div>
    </div>
  );
}
