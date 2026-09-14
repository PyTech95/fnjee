import { useEffect, useState } from "react";
import { questionsApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Search, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

const DIFF_COLOR = { easy: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20", medium: "bg-amber-500/10 text-amber-600 border-amber-500/20", hard: "bg-red-500/10 text-red-600 border-red-500/20" };

export default function QuestionBank() {
  const [rows, setRows] = useState([]);
  const [filters, setFilters] = useState({ subject: "", difficulty: "", q_type: "", search: "" });
  const [loading, setLoading] = useState(false);

  const load = () => {
    setLoading(true);
    const params = {};
    Object.entries(filters).forEach(([k, v]) => { if (v && v !== "all") params[k] = v; });
    questionsApi.list(params).then(setRows).finally(() => setLoading(false));
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [filters]);

  const remove = async (id) => {
    if (!confirm("Delete this question?")) return;
    await questionsApi.remove(id); toast.success("Deleted"); load();
  };

  return (
    <div data-testid="question-bank-page" className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Content</div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">Question Bank</h1>
          <p className="text-muted-foreground mt-1">Every question, tagged and ready to build a test.</p>
        </div>
        <div className="flex gap-2">
          <Link to="/admin/questions/new"><Button data-testid="new-question-btn" className="rounded-full">+ New question</Button></Link>
          <Link to="/admin/import"><Button data-testid="go-import-btn" variant="outline" className="rounded-full">Bulk import</Button></Link>
        </div>
      </div>

      <Card className="en-card p-4">
        <div className="grid md:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="absolute top-2.5 left-3 h-4 w-4 text-muted-foreground" />
            <Input data-testid="search-question" placeholder="Search text…" className="pl-9" value={filters.search}
              onChange={(e) => setFilters({...filters, search: e.target.value})} />
          </div>
          <Select value={filters.subject || "all"} onValueChange={(v) => setFilters({...filters, subject: v === "all" ? "" : v})}>
            <SelectTrigger data-testid="filter-subject"><SelectValue placeholder="Subject" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All subjects</SelectItem>
              <SelectItem value="Physics">Physics</SelectItem>
              <SelectItem value="Chemistry">Chemistry</SelectItem>
              <SelectItem value="Mathematics">Mathematics</SelectItem>
              <SelectItem value="Biology">Biology</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filters.difficulty || "all"} onValueChange={(v) => setFilters({...filters, difficulty: v === "all" ? "" : v})}>
            <SelectTrigger><SelectValue placeholder="Difficulty" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All levels</SelectItem>
              <SelectItem value="easy">Easy</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="hard">Hard</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filters.q_type || "all"} onValueChange={(v) => setFilters({...filters, q_type: v === "all" ? "" : v})}>
            <SelectTrigger><SelectValue placeholder="Type" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              <SelectItem value="mcq_single">MCQ (single)</SelectItem>
              <SelectItem value="mcq_multi">MCQ (multi)</SelectItem>
              <SelectItem value="true_false">True/False</SelectItem>
              <SelectItem value="integer">Integer</SelectItem>
              <SelectItem value="assertion_reason">Assertion-Reason</SelectItem>
              <SelectItem value="subjective">Subjective</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </Card>

      <Card className="en-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Question</TableHead>
              <TableHead>Subject</TableHead>
              <TableHead>Chapter</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Difficulty</TableHead>
              <TableHead className="text-right">Marks</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground py-8">Loading…</TableCell></TableRow>}
            {!loading && rows.length === 0 && <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground py-8">No questions yet. Try the Import Wizard.</TableCell></TableRow>}
            {rows.map((r) => (
              <TableRow key={r.id} data-testid={`qrow-${r.id}`}>
                <TableCell className="max-w-md"><div className="font-medium line-clamp-2">{r.text}</div></TableCell>
                <TableCell><Badge variant="secondary" className="rounded-full">{r.subject}</Badge></TableCell>
                <TableCell className="text-sm text-muted-foreground">{r.chapter || "—"}</TableCell>
                <TableCell className="text-xs">{r.type}</TableCell>
                <TableCell><Badge className={`rounded-full border ${DIFF_COLOR[r.difficulty] || ""}`} variant="outline">{r.difficulty}</Badge></TableCell>
                <TableCell className="text-right font-medium">{r.marks}</TableCell>
                <TableCell className="text-right">
                  <Button data-testid={`delete-q-${r.id}`} size="icon" variant="ghost" onClick={() => remove(r.id)}><Trash2 className="h-4 w-4 text-destructive" /></Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
