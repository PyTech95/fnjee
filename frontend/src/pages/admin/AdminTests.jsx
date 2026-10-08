import { useEffect, useState } from "react";
import { testsApi, usersApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Trash2, UserPlus } from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Link } from "react-router-dom";

export default function AdminTests() {
  const [rows, setRows] = useState([]);
  const [students, setStudents] = useState([]);
  const [active, setActive] = useState(null);
  const [picked, setPicked] = useState([]);

  const load = () => testsApi.list().then(setRows);
  useEffect(() => { load(); usersApi.list("student").then(setStudents); }, []);

  const remove = async (id) => {
    if (!confirm("Delete this test?")) return;
    await testsApi.remove(id); toast.success("Deleted"); load();
  };

  const assign = async () => {
    if (!picked.length) return toast.error("Select students");
    await testsApi.assign({ test_id: active.id, student_ids: picked });
    toast.success(`Assigned to ${picked.length} student(s)`);
    setActive(null); setPicked([]); load();
  };

  return (
    <div data-testid="admin-tests-page" className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Exams</div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">All tests</h1>
        </div>
        <Link to="/admin/tests/new"><Button data-testid="new-test-btn" className="rounded-full">+ New test</Button></Link>
      </div>

      <Card className="en-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead className="text-right">Questions</TableHead>
              <TableHead className="text-right">Assigned</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map(r => (
              <TableRow key={r.id}>
                <TableCell className="font-medium">{r.title}</TableCell>
                <TableCell><Badge variant="secondary" className="rounded-full">{r.exam_type}</Badge></TableCell>
                <TableCell>{r.duration_minutes} min</TableCell>
                <TableCell className="text-right">{r.question_ids?.length || 0}</TableCell>
                <TableCell className="text-right">{r.assigned_to?.length || 0}</TableCell>
                <TableCell className="text-right space-x-1">
                  <Button data-testid={`assign-test-${r.id}`} size="icon" variant="ghost" onClick={() => { setActive(r); setPicked(r.assigned_to || []); }}>
                    <UserPlus className="h-4 w-4" />
                  </Button>
                  <Button size="icon" variant="ghost" onClick={() => remove(r.id)}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {rows.length === 0 && <TableRow><TableCell colSpan={6} className="text-center py-8 text-muted-foreground">No tests yet.</TableCell></TableRow>}
          </TableBody>
        </Table>
      </Card>

      <Dialog open={!!active} onOpenChange={(v) => !v && setActive(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Assign test to students</DialogTitle></DialogHeader>
          <div className="max-h-80 overflow-y-auto en-scroll space-y-2">
            {students.map(s => (
              <label key={s.id} className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer ${picked.includes(s.id) ? "bg-primary/10" : "hover:bg-muted/60"}`}>
                <input type="checkbox" className="h-4 w-4 accent-primary" checked={picked.includes(s.id)}
                  onChange={(e) => setPicked(e.target.checked ? [...picked, s.id] : picked.filter(x => x !== s.id))} />
                <div className="flex-1">
                  <div className="font-medium text-sm">{s.name}</div>
                  <div className="text-xs text-muted-foreground">{s.email} · {s.exam_target}</div>
                </div>
              </label>
            ))}
          </div>
          <DialogFooter>
            <Button data-testid="confirm-assign" onClick={assign}>Assign to {picked.length}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
