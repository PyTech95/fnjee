import { useState } from "react";
import { importApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Upload, FileSpreadsheet, FileText, FileImage, CloudDownload, CheckCircle2, AlertTriangle, ClipboardPaste, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";

const FORMATS = [
  { icon: FileSpreadsheet, name: "Excel", exts: ".xlsx,.xls" },
  { icon: FileText, name: "Word", exts: ".docx" },
  { icon: FileImage, name: "PDF", exts: ".pdf" },
  { icon: FileText, name: "PageMaker", exts: ".pmd,.p65,.pm6,.pm7" },
  { icon: CloudDownload, name: "Google Drive", exts: "url" },
  { icon: ClipboardPaste, name: "Paste text", exts: "textarea" },
];

export default function ImportWizard() {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState(null);
  const [driveUrl, setDriveUrl] = useState("");
  const [rawText, setRawText] = useState("");
  const [source, setSource] = useState("file"); // file | drive | paste
  const [subjectDefault, setSubjectDefault] = useState("Physics");
  const [parsing, setParsing] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [parsed, setParsed] = useState(null);
  const [rows, setRows] = useState([]);
  const nav = useNavigate();

  const runParse = async () => {
    if (source === "file" && !file) return toast.error("Choose a file first");
    if (source === "drive" && !driveUrl) return toast.error("Enter a Google Drive URL");
    if (source === "paste" && rawText.trim().length < 30) return toast.error("Paste at least a few questions");
    setParsing(true);
    try {
      const fd = new FormData();
      if (source === "file") fd.append("file", file);
      if (source === "drive") fd.append("drive_url", driveUrl);
      if (source === "paste") fd.append("raw_text", rawText);
      fd.append("subject_default", subjectDefault);
      fd.append("use_ai", "true");
      const r = await importApi.parse(fd);
      setParsed(r);
      setRows(r.questions.map((q) => ({ ...q, _include: true })));
      setStep(3);
      if (r.count > 0) {
        const badge = r.used_regex && !r.used_ai ? " (fast regex)" : r.used_ai ? " (AI-assisted)" : "";
        toast.success(`Detected ${r.count} question(s)${badge}`);
      } else if (r.errors?.length) {
        toast.warning("No questions detected — see notes below");
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Extraction failed");
    } finally { setParsing(false); }
  };

  const commit = async () => {
    const selected = rows.filter((r) => r._include).map(({ _include, duplicate, id_tmp, ...rest }) => rest);
    if (!selected.length) return toast.error("Select at least one question");
    setCommitting(true);
    try {
      const r = await importApi.commit(selected);
      if (r.inserted > 0 && r.skipped > 0) {
        toast.success(`Saved ${r.inserted} · Skipped ${r.skipped} (empty or malformed)`);
      } else if (r.inserted > 0) {
        toast.success(`Saved ${r.inserted} question(s) to bank`);
      } else {
        toast.error(`Nothing saved. ${r.skipped_details?.[0]?.reason || "Please check the rows."}`);
        setCommitting(false); return;
      }
      nav("/admin/questions");
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Save failed");
    } finally { setCommitting(false); }
  };

  const updateRow = (i, patch) => setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  const addBlankRow = () => setRows((prev) => [...prev, {
    _include: true, type: "mcq_single", subject: subjectDefault, chapter: "", topic: "",
    difficulty: "medium", marks: 4, negative_marks: 1, text: "", options: ["", "", "", ""], correct: [],
    explanation: "", language: "English", status: "approved",
  }]);
  const removeRow = (i) => setRows((prev) => prev.filter((_, idx) => idx !== i));

  const includedCount = rows.filter((r) => r._include).length;

  return (
    <div data-testid="import-wizard-page" className="space-y-6 max-w-6xl mx-auto">
      <div>
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Import wizard</div>
        <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">Bring your question paper in.</h1>
        <p className="text-muted-foreground mt-1">Upload a file, paste text, or drop a Drive link. We extract with fast regex first — AI only kicks in when needed.</p>
      </div>

      <div className="flex items-center gap-4">
        {["Upload", "Detect & parse", "Review & save"].map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div data-testid={`step-${i + 1}`} className={`h-8 w-8 rounded-full grid place-items-center text-sm font-semibold ${step >= i + 1 ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>{i + 1}</div>
            <span className={`text-sm ${step >= i + 1 ? "text-foreground" : "text-muted-foreground"}`}>{s}</span>
            {i < 2 && <div className="w-8 h-px bg-border ml-2" />}
          </div>
        ))}
      </div>

      {step <= 2 && (
        <Card className="en-card p-6 space-y-6">
          <div>
            <Label className="text-sm font-semibold">Supported formats</Label>
            <div className="flex flex-wrap gap-2 mt-3">
              {FORMATS.map((f) => (
                <div key={f.name} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted text-sm">
                  <f.icon className="h-4 w-4 text-primary" /> {f.name}
                </div>
              ))}
            </div>
          </div>

          <Tabs value={source} onValueChange={setSource}>
            <TabsList data-testid="source-tabs" className="rounded-full">
              <TabsTrigger data-testid="tab-source-file" value="file" className="rounded-full">Upload file</TabsTrigger>
              <TabsTrigger data-testid="tab-source-paste" value="paste" className="rounded-full">Paste text</TabsTrigger>
              <TabsTrigger data-testid="tab-source-drive" value="drive" className="rounded-full">Drive link</TabsTrigger>
            </TabsList>
            <TabsContent value="file" className="mt-4">
              <label htmlFor="file-input" className="block cursor-pointer border-2 border-dashed border-border rounded-2xl p-10 text-center hover:border-primary transition-colors duration-200">
                <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
                <div className="mt-3 font-medium">{file ? file.name : "Click to choose a file"}</div>
                <div className="text-xs text-muted-foreground mt-1">Excel · Word · PDF · PageMaker</div>
                <input data-testid="file-input" id="file-input" type="file" className="hidden"
                  accept=".xlsx,.xls,.docx,.pdf,.pmd,.p65,.pm6,.pm7,.txt"
                  onChange={(e) => setFile(e.target.files?.[0] || null)} />
              </label>
            </TabsContent>
            <TabsContent value="paste" className="mt-4">
              <Label>Paste your questions here</Label>
              <Textarea data-testid="paste-textarea" value={rawText} onChange={(e) => setRawText(e.target.value)}
                rows={12} placeholder={`1. Which of the following is the SI unit of force?\n1) Watt   2) Newton   3) Joule   4) Pascal\n\n2. The value of g on the surface of Earth is …\n1) 8.9 m/s²   2) 9.8 m/s²   3) 10.1 m/s²   4) 11.2 m/s²\n\nAnswer Key:\n1) 2   2) 2`} />
              <p className="text-xs text-muted-foreground mt-2">Number your questions <b>1., 2., 3.</b> — options as <b>1) 2) 3) 4)</b> or <b>A. B. C. D.</b>. Add an answer key at the end for auto-marking.</p>
            </TabsContent>
            <TabsContent value="drive" className="mt-4">
              <Label>Public Google Drive link</Label>
              <Input data-testid="drive-url-input" value={driveUrl} onChange={(e) => setDriveUrl(e.target.value)}
                placeholder="https://drive.google.com/file/d/…/view" className="mt-1" />
              <p className="text-xs text-muted-foreground mt-2">Make sure the link is set to "Anyone with the link can view".</p>
            </TabsContent>
          </Tabs>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <Label>Default subject</Label>
              <Select value={subjectDefault} onValueChange={setSubjectDefault}>
                <SelectTrigger data-testid="default-subject"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Physics">Physics</SelectItem>
                  <SelectItem value="Chemistry">Chemistry</SelectItem>
                  <SelectItem value="Mathematics">Mathematics</SelectItem>
                  <SelectItem value="Biology">Biology</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex justify-end">
            <Button data-testid="parse-btn" onClick={runParse} disabled={parsing} className="rounded-full px-8">
              <Zap className="h-4 w-4 mr-2" /> {parsing ? "Extracting…" : "Upload & Extract Questions"}
            </Button>
          </div>
        </Card>
      )}

      {step === 3 && parsed && (
        <Card className="en-card p-6 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h3 className="font-display font-semibold text-lg">Review & save</h3>
              <div className="text-sm text-muted-foreground flex flex-wrap items-center gap-2">
                <span>{parsed.count} detected in <b>{parsed.filename}</b> · {includedCount} selected</span>
                {parsed.used_regex && <Badge variant="secondary" className="rounded-full">Fast regex</Badge>}
                {parsed.used_ai && <Badge variant="secondary" className="rounded-full">AI-assisted</Badge>}
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" className="rounded-full" onClick={addBlankRow} data-testid="add-blank-row">
                + Add question
              </Button>
              <Button variant="outline" className="rounded-full" onClick={() => { setStep(1); setParsed(null); setRows([]); }}>Start over</Button>
              <Button data-testid="commit-import" className="rounded-full" onClick={commit} disabled={committing || includedCount === 0}>
                <CheckCircle2 className="h-4 w-4 mr-2" /> {committing ? "Saving…" : `Submit & save ${includedCount} question(s)`}
              </Button>
            </div>
          </div>

          {parsed.errors?.length > 0 && (
            <div data-testid="parse-warnings" className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-900 dark:text-amber-200 text-sm space-y-1">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                <div className="space-y-1">{parsed.errors.slice(0, 4).map((e, i) => <div key={i}>{e}</div>)}</div>
              </div>
            </div>
          )}

          <div className="space-y-3 max-h-[65vh] overflow-y-auto en-scroll pr-1">
            {rows.map((r, i) => (
              <div key={i} data-testid={`review-row-${i}`}
                   className={`p-4 rounded-xl border ${r._include ? "border-primary/40 bg-primary/5" : "border-border"}`}>
                <div className="flex items-start gap-3">
                  <input data-testid={`row-check-${i}`} type="checkbox" checked={!!r._include}
                    onChange={(e) => updateRow(i, { _include: e.target.checked })}
                    className="mt-1.5 h-4 w-4 accent-primary" />
                  <div className="flex-1 space-y-3">
                    <div className="flex flex-wrap gap-2 items-center">
                      <Badge variant="secondary" className="rounded-full">{r.type}</Badge>
                      <Badge variant="outline" className="rounded-full">{r.subject}</Badge>
                      <Badge variant="outline" className="rounded-full">{r.difficulty}</Badge>
                      {r.duplicate && <Badge className="rounded-full bg-amber-500/10 text-amber-700 border-amber-500/30" variant="outline">Duplicate</Badge>}
                      <button onClick={() => removeRow(i)} className="ml-auto text-xs text-destructive hover:underline" data-testid={`remove-row-${i}`}>Remove</button>
                    </div>
                    <Textarea data-testid={`row-text-${i}`} value={r.text}
                      onChange={(e) => updateRow(i, { text: e.target.value })} className="text-sm" rows={2} />
                    {r.options?.length > 0 && (
                      <div className="grid sm:grid-cols-2 gap-2">
                        {r.options.map((opt, oi) => {
                          const letter = String.fromCharCode(65 + oi);
                          const isCorrect = (r.correct || []).includes(letter);
                          return (
                            <div key={oi} className="flex items-center gap-2">
                              <button onClick={() => {
                                const correct = new Set(r.correct || []);
                                if (isCorrect) correct.delete(letter); else correct.add(letter);
                                updateRow(i, { correct: [...correct] });
                              }} data-testid={`row-${i}-opt-${letter}-toggle`}
                                className={`h-7 w-7 rounded-full text-xs font-bold grid place-items-center border shrink-0 ${
                                  isCorrect ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground"
                                }`}>{letter}</button>
                              <Input value={opt} data-testid={`row-${i}-opt-${letter}-input`}
                                onChange={(e) => { const opts = [...r.options]; opts[oi] = e.target.value; updateRow(i, { options: opts }); }} />
                            </div>
                          );
                        })}
                      </div>
                    )}
                    <div className="flex flex-wrap gap-3 text-xs items-center">
                      <div><b>Correct:</b> {(r.correct || []).join(", ") || "—"}</div>
                      <div><b>Marks:</b> {r.marks}</div>
                      <div><b>-ve:</b> {r.negative_marks}</div>
                      {r.chapter && <div><b>Chapter:</b> {r.chapter}</div>}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {rows.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                No questions parsed.
                <Button variant="link" onClick={addBlankRow} className="ml-2">Add one manually →</Button>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
