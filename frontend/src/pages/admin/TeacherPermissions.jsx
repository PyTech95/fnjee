import { useEffect, useState } from "react";
import { teacherApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ShieldCheck, Save, GraduationCap } from "lucide-react";
import { toast } from "sonner";

const SUBJECTS = ["Physics", "Chemistry", "Mathematics", "Biology"];
const EXAMS = ["JEE", "NEET", "UPSC", "SSC", "Olympiad"];
const CLASSES = ["9", "10", "11", "12"];

function Chip({ active, onClick, children, testid }) {
  return (
    <button data-testid={testid} type="button" onClick={onClick}
      className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${active ? "bg-primary text-primary-foreground border-primary" : "border-border hover:bg-muted"}`}>
      {children}
    </button>
  );
}

function TeacherCard({ teacher, onSaved }) {
  const p = teacher.teacher_perms || {};
  const [subjects, setSubjects] = useState(p.subjects || []);
  const [exams, setExams] = useState(p.exams || []);
  const [classes, setClasses] = useState(p.classes || []);
  const [canPrint, setCanPrint] = useState(p.can_print !== false);
  const [canView, setCanView] = useState(p.can_view_results !== false);
  const [saving, setSaving] = useState(false);

  const tog = (list, setList, v) => setList(list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);

  const save = async () => {
    setSaving(true);
    try {
      await teacherApi.setPerms({ teacher_id: teacher.id, subjects, exams, classes, can_print: canPrint, can_view_results: canView });
      toast.success(`Access updated for ${teacher.name}`);
      onSaved?.();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed to save"); }
    finally { setSaving(false); }
  };

  const initials = (teacher.name || "T").split(" ").map((x) => x[0]).slice(0, 2).join("").toUpperCase();

  return (
    <Card data-testid={`teacher-card-${teacher.id}`} className="en-card p-5 space-y-4">
      <div className="flex items-center gap-3">
        <Avatar className="h-11 w-11"><AvatarImage src={teacher.avatar} /><AvatarFallback>{initials}</AvatarFallback></Avatar>
        <div>
          <div className="font-display font-bold text-lg leading-none">{teacher.name}</div>
          <div className="text-xs text-muted-foreground mt-1">{teacher.email}</div>
        </div>
      </div>

      <div>
        <Label className="text-xs uppercase tracking-wide text-muted-foreground">Subjects <span className="normal-case">(none = all)</span></Label>
        <div className="flex flex-wrap gap-2 mt-2">
          {SUBJECTS.map((s) => <Chip key={s} testid={`perm-sub-${teacher.id}-${s}`} active={subjects.includes(s)} onClick={() => tog(subjects, setSubjects, s)}>{s}</Chip>)}
        </div>
      </div>
      <div>
        <Label className="text-xs uppercase tracking-wide text-muted-foreground">Exams</Label>
        <div className="flex flex-wrap gap-2 mt-2">
          {EXAMS.map((e) => <Chip key={e} testid={`perm-exam-${teacher.id}-${e}`} active={exams.includes(e)} onClick={() => tog(exams, setExams, e)}>{e}</Chip>)}
        </div>
      </div>
      <div>
        <Label className="text-xs uppercase tracking-wide text-muted-foreground">Classes</Label>
        <div className="flex flex-wrap gap-2 mt-2">
          {CLASSES.map((c) => <Chip key={c} testid={`perm-class-${teacher.id}-${c}`} active={classes.includes(c)} onClick={() => tog(classes, setClasses, c)}>Class {c}</Chip>)}
        </div>
      </div>

      <div className="flex flex-wrap gap-6 pt-1">
        <div className="flex items-center gap-2"><Switch data-testid={`perm-print-${teacher.id}`} checked={canPrint} onCheckedChange={setCanPrint} /><span className="text-sm">Can print papers</span></div>
        <div className="flex items-center gap-2"><Switch data-testid={`perm-results-${teacher.id}`} checked={canView} onCheckedChange={setCanView} /><span className="text-sm">Can view results</span></div>
      </div>

      <Button data-testid={`perm-save-${teacher.id}`} className="rounded-full" disabled={saving} onClick={save}>
        <Save className="h-4 w-4 mr-2" />{saving ? "Saving…" : "Save access"}
      </Button>
    </Card>
  );
}

export default function TeacherPermissions() {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => { setLoading(true); teacherApi.list().then(setTeachers).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []);

  return (
    <div data-testid="teacher-permissions-page" className="space-y-6">
      <div>
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary flex items-center gap-1"><ShieldCheck className="h-3.5 w-3.5" /> Access control</div>
        <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">Teacher Permissions</h1>
        <p className="text-muted-foreground mt-1">Control which exams, subjects and classes each teacher can access.</p>
      </div>

      {loading && <div className="text-muted-foreground">Loading…</div>}
      {!loading && teachers.length === 0 && (
        <Card className="en-card p-10 text-center">
          <GraduationCap className="h-8 w-8 mx-auto text-primary/50" />
          <div className="mt-3 font-medium">No teachers yet</div>
          <p className="text-sm text-muted-foreground mt-1">Teachers can register from the login page (Teacher tab).</p>
        </Card>
      )}
      <div className="grid lg:grid-cols-2 gap-5">
        {teachers.map((t) => <TeacherCard key={t.id} teacher={t} onSaved={load} />)}
      </div>
    </div>
  );
}
