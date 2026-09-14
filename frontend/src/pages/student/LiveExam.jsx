import { useEffect, useMemo, useState, useRef, useCallback } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { testsApi, attemptsApi, proctorApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { toast } from "sonner";
import {
  Clock, Flag, ChevronLeft, ChevronRight, CheckCircle2,
  Maximize2, Minimize2, Calculator, StickyNote, Keyboard,
  Focus, Bookmark, ChevronUp, LayoutGrid, XCircle, Timer, Lightbulb
} from "lucide-react";
import confetti from "canvas-confetti";
import MathText from "@/components/MathText";

const LETTERS = ["A", "B", "C", "D", "E", "F"];
const FONT_STEPS = ["text-sm", "text-base", "text-lg", "text-xl"];

export default function LiveExam() {
  const { testId } = useParams();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const useRetakePass = searchParams.get("retake") === "1";
  const [test, setTest] = useState(null);
  const [attempt, setAttempt] = useState(null);
  const [answers, setAnswers] = useState({});    // qid -> { answer:[], marked }
  const [timePerQ, setTimePerQ] = useState({});  // qid -> seconds
  const [hints, setHints] = useState({});        // qid -> hint text
  const [hintLoading, setHintLoading] = useState(false);
  const [current, setCurrent] = useState(0);
  const [remaining, setRemaining] = useState(0);
  const [fontSize, setFontSize] = useState(1);   // index into FONT_STEPS
  const [focusMode, setFocusMode] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [calcOpen, setCalcOpen] = useState(false);
  const [padOpen, setPadOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [notes, setNotes] = useState("");
  const [activeSection, setActiveSection] = useState(null);
  const [violations, setViolations] = useState(0);
  const violationsRef = useRef(0);
  const submitted = useRef(false);
  const qStartRef = useRef(Date.now());
  const milestone5 = useRef(0);

  /* ---------------- load test + start attempt ---------------- */
  useEffect(() => {
    let iv, cancelled = false;
    (async () => {
      try {
        const t = await testsApi.get(testId, true);
        if (cancelled) return;
        setTest(t);
        const a = await attemptsApi.start(testId, useRetakePass);
        if (cancelled) return;
        setAttempt(a);
        if (a.status === "submitted") { nav(`/student/results/${a.id}`, { replace: true }); return; }
        const end = new Date(a.ends_at).getTime();
        // Guard: if the returned in-progress attempt is already expired (stale server state),
        // auto-submit it so the student isn't stuck with a 00:00:00 timer.
        if (end <= Date.now()) {
          try {
            const r = await attemptsApi.submit({ attempt_id: a.id, answers: [] });
            nav(`/student/results/${r.id}`, { replace: true });
          } catch { nav("/student/tests", { replace: true }); }
          return;
        }
        const tick = () => setRemaining(Math.max(0, Math.floor((end - Date.now()) / 1000)));
        tick(); iv = setInterval(tick, 1000);
      } catch {
        toast.error("Failed to start"); nav("/student/tests", { replace: true });
      }
    })();
    return () => { cancelled = true; if (iv) clearInterval(iv); };
  }, [testId, nav]);

  /* ---------------- anti-cheat + Trust Score proctoring ---------------- */
  useEffect(() => {
    if (!attempt || attempt.status === "submitted") return;
    const send = (type) => {
      proctorApi.event(attempt.id, type).then((res) => {
        if (res?.action === "auto_submit" && !submitted.current) {
          submitted.current = true;
          toast.error("Trust score too low — your attempt is being auto-submitted.");
          finalSubmit(true);
        } else if (res?.action === "flag") {
          toast.error("You have been flagged for proctor review.");
        }
      }).catch(() => {});
    };
    const flag = (reason, type) => {
      violationsRef.current += 1;
      setViolations(violationsRef.current);
      toast.warning(`Proctoring alert: ${reason}. (${violationsRef.current})`);
      if (type) send(type);
    };
    const onVis = () => { if (document.hidden) flag("you switched away from the exam", "tab_switch"); };
    const onBlur = () => flag("the exam window lost focus", "window_blur");
    const noContext = (e) => { e.preventDefault(); flag("right-click is disabled", "right_click"); };
    const noCopy = (e) => { e.preventDefault(); flag("copying is disabled", "copy"); };
    const noPaste = (e) => { e.preventDefault(); flag("pasting is disabled", "paste"); };
    const onFsExit = () => { if (!document.fullscreenElement) flag("you exited fullscreen", "fullscreen_exit"); };
    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("blur", onBlur);
    document.addEventListener("contextmenu", noContext);
    document.addEventListener("copy", noCopy);
    document.addEventListener("paste", noPaste);
    document.addEventListener("fullscreenchange", onFsExit);
    return () => {
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("blur", onBlur);
      document.removeEventListener("contextmenu", noContext);
      document.removeEventListener("copy", noCopy);
      document.removeEventListener("paste", noPaste);
      document.removeEventListener("fullscreenchange", onFsExit);
    };
  }, [attempt]);

  const questions = test?.questions || [];
  const q = questions[current];

  /* ---------------- per-question time tracking ---------------- */
  useEffect(() => {
    qStartRef.current = Date.now();
    return () => {
      if (!q) return;
      const spent = Math.round((Date.now() - qStartRef.current) / 1000);
      setTimePerQ(prev => ({ ...prev, [q.id]: (prev[q.id] || 0) + spent }));
    };
    // eslint-disable-next-line
  }, [current, q?.id]);

  /* ---------------- fullscreen listener ---------------- */
  useEffect(() => {
    const onFs = () => setFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", onFs);
    return () => document.removeEventListener("fullscreenchange", onFs);
  }, []);

  /* ---------------- section derivation ---------------- */
  const sections = useMemo(() => {
    if (!test) return [];
    if (test.sections?.length) return test.sections.map(s => ({ ...s, indices: s.question_ids.map(qid => questions.findIndex(x => x.id === qid)).filter(i => i >= 0) }));
    return [{ name: "All", indices: questions.map((_, i) => i) }];
  }, [test, questions]);

  useEffect(() => {
    if (sections.length && activeSection == null) setActiveSection(0);
  }, [sections, activeSection]);

  /* ---------------- setters ---------------- */
  const setAnswer = useCallback((qid, arr) => {
    setAnswers(prev => {
      const wasAnswered = prev[qid]?.answer?.length > 0;
      const next = { ...prev, [qid]: { ...(prev[qid] || {}), answer: arr } };
      const nowAnswered = arr?.length > 0;
      const total = Object.values(next).filter(a => a?.answer?.length).length;
      // celebrate every 5 answers
      if (!wasAnswered && nowAnswered && total > milestone5.current && total % 5 === 0) {
        milestone5.current = total;
        toast.success(`🔥 ${total} down. Keep going!`, { duration: 1400 });
      }
      return next;
    });
  }, []);
  const toggleMark = useCallback((qid) => setAnswers(prev => ({ ...prev, [qid]: { ...(prev[qid] || { answer: [] }), marked: !prev[qid]?.marked } })), []);
  const setConfidence = useCallback((qid, v) => setAnswers(prev => ({ ...prev, [qid]: { ...(prev[qid] || { answer: [] }), confidence: prev[qid]?.confidence === v ? null : v } })), []);
  const clearAnswer = useCallback((qid) => setAnswers(prev => ({ ...prev, [qid]: { ...(prev[qid] || {}), answer: [] } })), []);

  /* ---------------- submit ---------------- */
  const finalSubmit = async (auto = false) => {
    if (submitted.current && !auto) return;
    submitted.current = true;
    // commit current question's time (compute synchronously for payload)
    const finalTimes = { ...timePerQ };
    if (q) {
      const spent = Math.round((Date.now() - qStartRef.current) / 1000);
      finalTimes[q.id] = (finalTimes[q.id] || 0) + spent;
      setTimePerQ(finalTimes);
    }
    try {
      const payload = {
        attempt_id: attempt.id,
        answers: questions.map(x => ({
          question_id: x.id,
          answer: answers[x.id]?.answer || [],
          marked_review: !!answers[x.id]?.marked,
          confidence: answers[x.id]?.confidence || null,
          image_answer: answers[x.id]?.image_answer || null,
          time_taken: finalTimes[x.id] || 0,
        })),
      };
      const r = await attemptsApi.submit(payload);
      // stash timePerQ locally so Result can pick it up
      try { sessionStorage.setItem(`tpq_${r.id}`, JSON.stringify(finalTimes)); } catch {}
      // complete any active duel
      try {
        const duelCode = localStorage.getItem("active_duel");
        if (duelCode) {
          const { duelsApi } = await import("@/lib/api");
          await duelsApi.complete(duelCode, r.id).catch(() => {});
          localStorage.removeItem("active_duel");
        }
      } catch {}
      toast.success(auto ? "Time up — auto-submitted" : "Submitted!");
      nav(`/student/results/${r.id}`);
    } catch { toast.error("Submit failed"); submitted.current = false; }
  };

  /* ---------------- keyboard shortcuts ---------------- */
  useEffect(() => {
    const onKey = (e) => {
      if (["INPUT", "TEXTAREA"].includes(e.target.tagName)) return;
      if (!q) return;
      const key = e.key.toLowerCase();
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); finalSubmit(false); return; }
      if (["1", "2", "3", "4"].includes(e.key)) {
        e.preventDefault();
        const idx = parseInt(e.key, 10) - 1;
        const opts = q.type === "true_false" ? ["True", "False"] : (q.options || []);
        if (idx < opts.length) toggleOption(LETTERS[idx]);
      } else if (key === "n" || e.key === "ArrowRight") {
        e.preventDefault(); setCurrent(c => Math.min(questions.length - 1, c + 1));
      } else if (key === "p" || e.key === "ArrowLeft") {
        e.preventDefault(); setCurrent(c => Math.max(0, c - 1));
      } else if (key === "m") { e.preventDefault(); toggleMark(q.id); }
      else if (key === "c") { e.preventDefault(); clearAnswer(q.id); }
      else if (key === "f") { e.preventDefault(); setFocusMode(v => !v); }
      else if (key === "?" || (e.shiftKey && e.key === "/")) { e.preventDefault(); setHelpOpen(v => !v); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line
  }, [q, questions.length, answers]);

  const toggleOption = (letter) => {
    if (!q) return;
    const isSingle = q.type === "mcq_single" || q.type === "true_false" || q.type === "assertion_reason";
    const selected = answers[q.id]?.answer || [];
    if (isSingle) setAnswer(q.id, [letter]);
    else setAnswer(q.id, selected.includes(letter) ? selected.filter(x => x !== letter) : [...selected, letter]);
  };

  const goFullscreen = () => {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
    else document.exitFullscreen?.();
  };

  const useHint = async () => {
    if (!q || !attempt) return;
    if (hints[q.id]) return;
    setHintLoading(true);
    try {
      const res = await attemptsApi.hint(attempt.id, q.id);
      setHints(prev => ({ ...prev, [q.id]: res.hint }));
      toast.success(res.charged ? `Hint unlocked · ${res.hint_tokens_left} tokens left` : "Hint revealed");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not get a hint");
    } finally { setHintLoading(false); }
  };

  const statusFor = (i) => {
    const qi = questions[i]; if (!qi) return "unattempted";
    const a = answers[qi.id];
    if (a?.marked && a.answer?.length) return "answered-marked";
    if (a?.marked) return "marked";
    if (a?.answer?.length) return "answered";
    return "unattempted";
  };

  const timeStr = useMemo(() => {
    const h = Math.floor(remaining / 3600), m = Math.floor((remaining % 3600) / 60), s = remaining % 60;
    return [h, m, s].map(n => String(n).padStart(2, "0")).join(":");
  }, [remaining]);

  const timeCritical = remaining > 0 && remaining < 300;

  /* ---------------- auto submit on time out ---------------- */
  useEffect(() => {
    if (remaining === 0 && attempt && !submitted.current && test) {
      submitted.current = true;
      finalSubmit(true);
    }
    // eslint-disable-next-line
  }, [remaining]);

  /* ---------------- early states ---------------- */
  if (!test || !attempt) return <div data-testid="exam-loading" className="min-h-screen grid place-items-center text-muted-foreground">Loading exam…</div>;
  if (questions.length === 0) {
    return (
      <div data-testid="exam-empty" className="min-h-screen grid place-items-center px-6">
        <Card className="en-card p-8 max-w-md text-center">
          <div className="font-display font-semibold text-xl">No questions in this test</div>
          <p className="text-sm text-muted-foreground mt-2">Ask your admin to add some, or pick a different test.</p>
          <Button data-testid="back-to-tests" className="rounded-full mt-4" onClick={() => nav("/student/tests", { replace: true })}>Back to tests</Button>
        </Card>
      </div>
    );
  }
  if (!q) return <div className="min-h-screen grid place-items-center text-muted-foreground">Loading question…</div>;

  const isSingle = q.type === "mcq_single" || q.type === "true_false" || q.type === "assertion_reason";
  const isMulti = q.type === "mcq_multi";
  const isInteger = q.type === "integer";
  const options = q.type === "true_false" ? ["True", "False"] : (q.options || []);
  const selected = answers[q.id]?.answer || [];

  const totalAnswered = Object.values(answers).filter(a => a?.answer?.length).length;
  const totalMarked = Object.values(answers).filter(a => a?.marked).length;
  const progressPct = Math.round((totalAnswered / questions.length) * 100);
  const spentOnQ = Math.round((Date.now() - qStartRef.current) / 1000);

  return (
    <TooltipProvider delayDuration={200}>
    <div data-testid="live-exam-page" className={`min-h-screen bg-background ${FONT_STEPS[fontSize]}`}>
      {/* ---------- TOP BAR ---------- */}
      <div className="sticky top-0 z-40 backdrop-blur-xl bg-background/95 border-b border-border">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 h-14 flex items-center gap-3">
          <div className="min-w-0 shrink">
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Live · {test.exam_type.replace("_", " ")}</div>
            <div className="font-display font-semibold text-sm truncate">{test.title}</div>
          </div>
          {violations > 0 && (
            <Badge data-testid="proctor-violations" variant="outline" className="rounded-full border-red-500/40 bg-red-500/10 text-red-600 gap-1 shrink-0">
              <XCircle className="h-3 w-3" /> {violations}
            </Badge>
          )}
          {/* section tabs */}
          {sections.length > 1 && (
            <div className="hidden md:flex items-center gap-1 ml-4 overflow-x-auto en-scroll">
              {sections.map((s, i) => {
                const answered = s.indices.filter(idx => answers[questions[idx]?.id]?.answer?.length).length;
                return (
                  <button key={s.name} data-testid={`section-tab-${i}`}
                    onClick={() => { const first = s.indices[0]; if (first != null) { setCurrent(first); setActiveSection(i); }}}
                    className={`rounded-full px-3 py-1 text-xs font-medium whitespace-nowrap transition-colors duration-150 ${activeSection === i ? "bg-primary text-primary-foreground" : "bg-muted text-foreground/70 hover:bg-muted/80"}`}>
                    {s.name} <span className="opacity-70 ml-1">{answered}/{s.indices.length}</span>
                  </button>
                );
              })}
            </div>
          )}
          <div className="flex-1" />
          {/* timer */}
          <div className={`flex items-center gap-2 rounded-full px-3 py-1.5 font-mono font-bold text-base sm:text-lg tabular-nums ${timeCritical ? "bg-destructive/15 text-destructive animate-pulse" : "bg-primary/10 text-primary"}`}>
            <Clock className="h-4 w-4" /> <span data-testid="exam-timer">{timeStr}</span>
          </div>
          {/* action icons */}
          <div className="hidden sm:flex items-center gap-1">
            <IconBtn testid="btn-font-dec" onClick={() => setFontSize(f => Math.max(0, f - 1))} label="Smaller text (—)"><span className="text-xs font-bold">A-</span></IconBtn>
            <IconBtn testid="btn-font-inc" onClick={() => setFontSize(f => Math.min(FONT_STEPS.length - 1, f + 1))} label="Larger text (+)"><span className="text-sm font-bold">A+</span></IconBtn>
            <IconBtn testid="btn-focus" active={focusMode} onClick={() => setFocusMode(v => !v)} label={focusMode ? "Exit focus mode (F)" : "Focus mode (F)"}><Focus className="h-4 w-4" /></IconBtn>
            <IconBtn testid="btn-calc" onClick={() => setCalcOpen(true)} label="Calculator"><Calculator className="h-4 w-4" /></IconBtn>
            <IconBtn testid="btn-pad" onClick={() => setPadOpen(true)} label="Scratchpad"><StickyNote className="h-4 w-4" /></IconBtn>
            <IconBtn testid="btn-fullscreen" onClick={goFullscreen} label={fullscreen ? "Exit fullscreen" : "Fullscreen"}>{fullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}</IconBtn>
            <IconBtn testid="btn-help" onClick={() => setHelpOpen(true)} label="Keyboard shortcuts (?)"><Keyboard className="h-4 w-4" /></IconBtn>
          </div>
          <Button data-testid="final-submit-btn" className="rounded-full shrink-0" onClick={() => finalSubmit(false)}>
            <CheckCircle2 className="h-4 w-4 mr-1.5" /> Submit
          </Button>
        </div>
        {/* progress bar */}
        <div className="h-1 bg-muted">
          <div className="h-full bg-primary transition-all duration-500" style={{ width: `${progressPct}%` }} data-testid="progress-bar" />
        </div>
      </div>

      {/* ---------- BODY ---------- */}
      <div className="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-6 grid lg:grid-cols-12 gap-4 lg:gap-6 pb-24 lg:pb-6">
        {/* main question */}
        <div className={`${focusMode ? "lg:col-span-12" : "lg:col-span-8"}`}>
          <Card className="en-card p-5 sm:p-7 en-fade-up" key={q.id}>
            <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary" className="rounded-full">Q{current + 1} / {questions.length}</Badge>
                <Badge variant="outline" className="rounded-full">{q.subject}</Badge>
                <Badge variant="outline" className="rounded-full capitalize">{q.difficulty}</Badge>
                <Badge variant="outline" className="rounded-full">+{q.marks} / -{q.negative_marks || 0}</Badge>
                {q.chapter && <Badge variant="outline" className="rounded-full text-xs">{q.chapter}</Badge>}
              </div>
              <div className="flex items-center gap-2">
                <Tooltip><TooltipTrigger asChild>
                  <div className="text-xs text-muted-foreground flex items-center gap-1"><Timer className="h-3.5 w-3.5" />{spentOnQ}s</div>
                </TooltipTrigger><TooltipContent>Time on this question</TooltipContent></Tooltip>
                <button data-testid="mark-review-btn" onClick={() => toggleMark(q.id)}
                  className={`rounded-full px-3 py-1 text-xs font-medium flex items-center gap-1 transition-colors duration-150 ${answers[q.id]?.marked ? "bg-accent text-accent-foreground" : "bg-muted hover:bg-muted/70"}`}>
                  <Flag className={`h-3.5 w-3.5 ${answers[q.id]?.marked ? "fill-current" : ""}`} /> Mark
                </button>
                {/* Confidence tap */}
                <div className="flex rounded-full bg-muted p-0.5 text-[10px] font-semibold">
                  <button data-testid="confidence-sure" onClick={() => setConfidence(q.id, "sure")}
                    className={`px-2.5 py-1 rounded-full transition-colors duration-150 ${answers[q.id]?.confidence === "sure" ? "bg-emerald-500 text-white" : "text-muted-foreground hover:text-foreground"}`}>SURE</button>
                  <button data-testid="confidence-guess" onClick={() => setConfidence(q.id, "guess")}
                    className={`px-2.5 py-1 rounded-full transition-colors duration-150 ${answers[q.id]?.confidence === "guess" ? "bg-amber-500 text-white" : "text-muted-foreground hover:text-foreground"}`}>GUESS</button>
                </div>
              </div>
            </div>
            <div className="leading-relaxed whitespace-pre-wrap"><MathText>{q.text}</MathText></div>
            {q.image_url && <img src={q.image_url} alt="question" className="mt-4 rounded-xl border border-border max-h-80 object-contain" loading="lazy" />}
            {hints[q.id] && (
              <div data-testid="hint-box" className="mt-4 rounded-2xl border border-amber-300 bg-amber-50 dark:bg-amber-500/10 p-4 flex gap-3">
                <Lightbulb className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
                <div><div className="text-xs font-bold uppercase tracking-widest text-amber-600 mb-1">Hint</div><div className="text-sm"><MathText>{hints[q.id]}</MathText></div></div>
              </div>
            )}
            <div className="mt-6 space-y-3">
              {(isSingle || isMulti) && options.map((opt, i) => {
                const letter = LETTERS[i];
                const isSel = selected.includes(letter);
                return (
                  <button key={i} data-testid={`option-${letter}`} type="button" onClick={() => toggleOption(letter)}
                    className={`w-full text-left p-4 rounded-2xl border-2 flex items-start gap-3 transition-all duration-150 hover:-translate-y-0.5 ${isSel ? "border-primary bg-primary/10 shadow-sm shadow-primary/20" : "border-border hover:border-primary/50"}`}>
                    <div className={`h-9 w-9 shrink-0 rounded-xl grid place-items-center font-display font-bold text-base ${isSel ? "bg-primary text-primary-foreground" : "bg-muted"}`}>{letter}</div>
                    <div className="pt-1.5 flex-1"><MathText>{opt}</MathText></div>
                    <kbd className="hidden sm:inline-flex text-[10px] font-mono px-1.5 py-0.5 rounded bg-muted text-muted-foreground">{i + 1}</kbd>
                  </button>
                );
              })}
              {isInteger && (
                <div>
                  <label className="text-xs text-muted-foreground uppercase tracking-widest">Enter numeric answer</label>
                  <Input data-testid="integer-answer" value={selected[0] || ""} onChange={(e) => setAnswer(q.id, [e.target.value])} className="text-xl h-14 mt-2 rounded-2xl" autoFocus />
                </div>
              )}
              {q.type === "subjective" && (
                <SubjectiveAnswer
                  q={q}
                  answers={answers}
                  setAnswer={setAnswer}
                  setImageAnswer={(img) => setAnswers(prev => ({ ...prev, [q.id]: { ...(prev[q.id] || { answer: [] }), image_answer: img } }))}
                />
              )}
            </div>
            {/* action row */}
            <div className="flex items-center justify-between mt-6 gap-2">
              <div className="flex gap-2">
                <Button data-testid="prev-btn" variant="outline" className="rounded-full" onClick={() => setCurrent(c => Math.max(0, c - 1))} disabled={current === 0}><ChevronLeft className="h-4 w-4 mr-1" /> Prev</Button>
                <Button variant="ghost" className="rounded-full" onClick={() => clearAnswer(q.id)}><XCircle className="h-4 w-4 mr-1" />Clear</Button>
                <Button data-testid="use-hint-btn" variant="outline" className="rounded-full border-amber-400/60 text-amber-600 hover:bg-amber-50" onClick={useHint} disabled={hintLoading || !!hints[q.id]}>
                  <Lightbulb className="h-4 w-4 mr-1" />{hints[q.id] ? "Hint shown" : hintLoading ? "…" : "Use hint"}
                </Button>
              </div>
              <Button data-testid="next-btn" className="rounded-full" onClick={() => setCurrent(c => Math.min(questions.length - 1, c + 1))} disabled={current === questions.length - 1}>
                Save & next <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </Card>
        </div>

        {/* palette sidebar (desktop) */}
        {!focusMode && (
          <div className="hidden lg:block lg:col-span-4">
            <Palette questions={questions} current={current} setCurrent={setCurrent} statusFor={statusFor} answers={answers} totalAnswered={totalAnswered} totalMarked={totalMarked} />
          </div>
        )}
      </div>

      {/* ---------- MOBILE BOTTOM BAR ---------- */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-background/95 backdrop-blur-xl">
        <div className="px-3 py-2 flex items-center gap-2">
          <Button variant="outline" size="icon" className="rounded-full" onClick={() => setCurrent(c => Math.max(0, c - 1))} disabled={current === 0}><ChevronLeft className="h-4 w-4" /></Button>
          <Sheet open={paletteOpen} onOpenChange={setPaletteOpen}>
            <SheetTrigger asChild>
              <Button data-testid="mobile-palette-btn" variant="secondary" className="rounded-full flex-1"><LayoutGrid className="h-4 w-4 mr-2" /> Q{current + 1} / {questions.length} <span className="ml-auto text-xs opacity-70">{totalAnswered} done</span></Button>
            </SheetTrigger>
            <SheetContent side="bottom" className="max-h-[80vh] overflow-y-auto en-scroll">
              <SheetHeader className="mb-3"><SheetTitle>Question palette</SheetTitle></SheetHeader>
              <Palette questions={questions} current={current} setCurrent={(i) => { setCurrent(i); setPaletteOpen(false); }} statusFor={statusFor} answers={answers} totalAnswered={totalAnswered} totalMarked={totalMarked} mobile />
            </SheetContent>
          </Sheet>
          <Button size="icon" className="rounded-full" onClick={() => setCurrent(c => Math.min(questions.length - 1, c + 1))} disabled={current === questions.length - 1}><ChevronRight className="h-4 w-4" /></Button>
        </div>
      </div>

      {/* ---------- Calculator ---------- */}
      <Dialog open={calcOpen} onOpenChange={setCalcOpen}>
        <DialogContent className="max-w-xs">
          <DialogHeader><DialogTitle>Calculator</DialogTitle></DialogHeader>
          <Calc />
        </DialogContent>
      </Dialog>

      {/* ---------- Scratchpad ---------- */}
      <Dialog open={padOpen} onOpenChange={setPadOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle>Scratchpad</DialogTitle></DialogHeader>
          <Textarea data-testid="scratchpad" value={notes} onChange={(e) => setNotes(e.target.value)} rows={10} placeholder="Rough work stays here through the whole test…" className="rounded-xl font-mono text-sm" />
          <div className="text-xs text-muted-foreground">Not submitted — just for you.</div>
        </DialogContent>
      </Dialog>

      {/* ---------- Help ---------- */}
      <Dialog open={helpOpen} onOpenChange={setHelpOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle>Keyboard shortcuts</DialogTitle></DialogHeader>
          <div className="grid grid-cols-2 gap-2 text-sm">
            {[
              ["1 · 2 · 3 · 4", "Select option A / B / C / D"],
              ["N or →", "Next question"],
              ["P or ←", "Previous question"],
              ["M", "Mark for review"],
              ["C", "Clear answer"],
              ["F", "Toggle focus mode"],
              ["?", "Show these shortcuts"],
              ["⌘/Ctrl + Enter", "Submit test"],
            ].map(([k, v]) => (
              <div key={k} className="flex items-center gap-2">
                <kbd className="rounded bg-muted px-2 py-0.5 text-xs font-mono">{k}</kbd>
                <span className="text-muted-foreground text-xs">{v}</span>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
    </TooltipProvider>
  );
}

/* =============================================================== */
function IconBtn({ children, onClick, label, active, testid }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button data-testid={testid} onClick={onClick} aria-label={label}
          className={`h-9 w-9 rounded-full grid place-items-center transition-colors duration-150 ${active ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}>
          {children}
        </button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}

function Palette({ questions, current, setCurrent, statusFor, answers, totalAnswered, totalMarked, mobile }) {
  return (
    <Card className={`en-card p-5 ${mobile ? "" : "lg:sticky lg:top-20"}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display font-semibold text-base">Palette</h3>
        <div className="flex gap-2 text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded bg-emerald-500" />{totalAnswered}</span>
          <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded bg-accent" />{totalMarked}</span>
        </div>
      </div>
      <div className="grid grid-cols-6 gap-1.5 max-h-[60vh] overflow-y-auto en-scroll">
        {questions.map((qi, i) => {
          const st = statusFor(i);
          const cls =
            st === "answered" ? "bg-emerald-500 text-white border-emerald-500" :
            st === "marked" ? "bg-accent text-accent-foreground border-accent" :
            st === "answered-marked" ? "bg-secondary text-secondary-foreground border-secondary" :
            "bg-muted text-foreground border-border";
          return (
            <Tooltip key={qi.id}>
              <TooltipTrigger asChild>
                <button data-testid={`palette-${i}`} onClick={() => setCurrent(i)}
                  className={`h-9 rounded-lg border-2 font-display font-semibold text-xs transition-transform duration-150 hover:scale-105 ${cls} ${current === i ? "ring-2 ring-primary ring-offset-2 ring-offset-background" : ""}`}>
                  {i + 1}
                </button>
              </TooltipTrigger>
              <TooltipContent side="top">
                <div className="text-xs">{qi.subject} · {qi.difficulty}</div>
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
      <div className="mt-4 grid grid-cols-2 gap-1.5 text-[11px]">
        <Legend swatch="bg-emerald-500" label="Answered" />
        <Legend swatch="bg-accent" label="For review" />
        <Legend swatch="bg-secondary" label="Answered + review" />
        <Legend swatch="bg-muted" label="Not visited" />
      </div>
    </Card>
  );
}

/* Subjective answer — student can type OR write on notebook and upload a photo */
function SubjectiveAnswer({ q, answers, setAnswer, setImageAnswer }) {
  const val = answers[q.id]?.answer?.[0] || "";
  const img = answers[q.id]?.image_answer || "";
  const fileRef = useRef(null);
  const camRef = useRef(null);

  const handleFile = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (f.size > 4 * 1024 * 1024) { toast.error("Image too large (max 4 MB). Please compress and retry."); return; }
    const reader = new FileReader();
    reader.onload = () => setImageAnswer(String(reader.result || ""));
    reader.readAsDataURL(f);
  };

  return (
    <div data-testid="subjective-answer-block" className="space-y-4">
      <div>
        <label className="text-xs text-muted-foreground uppercase tracking-widest">Type your answer</label>
        <Textarea
          data-testid="subjective-textarea"
          value={val}
          onChange={(e) => setAnswer(q.id, [e.target.value])}
          rows={5}
          placeholder="Type here, or use the camera below to attach your handwritten notebook answer."
          className="mt-2 rounded-2xl"
        />
      </div>
      <div className="rounded-2xl border-2 border-dashed border-border p-4">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-muted-foreground uppercase tracking-widest">Or upload notebook answer</span>
          <div className="ml-auto flex gap-2">
            <input ref={camRef} data-testid="subjective-camera-input" type="file" accept="image/*" capture="environment" className="hidden" onChange={handleFile} />
            <input ref={fileRef} data-testid="subjective-file-input" type="file" accept="image/*" className="hidden" onChange={handleFile} />
            <Button data-testid="subjective-camera-btn" type="button" variant="outline" className="rounded-full" onClick={() => camRef.current?.click()}>
              Take photo
            </Button>
            <Button data-testid="subjective-file-btn" type="button" variant="outline" className="rounded-full" onClick={() => fileRef.current?.click()}>
              Choose image
            </Button>
          </div>
        </div>
        {img ? (
          <div className="mt-4">
            <img data-testid="subjective-image-preview" src={img} alt="handwritten answer" className="max-h-72 rounded-xl border border-border object-contain mx-auto" />
            <div className="mt-2 flex justify-end">
              <Button data-testid="subjective-image-remove" variant="ghost" size="sm" className="rounded-full text-destructive" onClick={() => setImageAnswer(null)}>
                Remove image
              </Button>
            </div>
          </div>
        ) : (
          <p className="mt-3 text-xs text-muted-foreground">
            Write your working on paper, snap a photo, and upload here. Your teacher will grade it manually.
          </p>
        )}
      </div>
    </div>
  );
}

function Legend({ swatch, label }) {
  return <div className="flex items-center gap-1.5"><div className={`h-3 w-3 rounded ${swatch}`} /><span className="text-muted-foreground">{label}</span></div>;
}

/* Simple in-exam calculator (basic 4-fn + sqrt / pi) */
function Calc() {
  const [expr, setExpr] = useState("");
  const [result, setResult] = useState("");
  const push = (v) => setExpr(e => e + v);
  const clr = () => { setExpr(""); setResult(""); };
  const back = () => setExpr(e => e.slice(0, -1));
  const evalIt = () => {
    try {
      // safe-ish: only allow digits, operators, dot, parens, and math functions
      const safe = expr.replace(/π/g, "Math.PI").replace(/√/g, "Math.sqrt");
      if (!/^[-+/*().\d\s%eE\w]+$/.test(safe.replace(/Math\.\w+/g, ""))) throw new Error("bad");
      // eslint-disable-next-line no-new-func
      const r = Function(`"use strict"; return (${safe})`)();
      setResult(String(r));
    } catch { setResult("Error"); }
  };
  const btn = (label, on, cls = "") => (
    <button key={label} data-testid={`calc-${label}`} onClick={on} className={`h-11 rounded-xl bg-muted hover:bg-muted/70 font-semibold ${cls}`}>{label}</button>
  );
  return (
    <div>
      <div className="rounded-xl bg-muted/50 p-3 font-mono text-right min-h-[3.5rem]">
        <div className="text-xs text-muted-foreground truncate">{expr || "0"}</div>
        <div className="text-2xl font-bold">{result || "="}</div>
      </div>
      <div className="grid grid-cols-4 gap-1.5 mt-3">
        {btn("C", clr, "bg-destructive/10 text-destructive")}
        {btn("⌫", back)}
        {btn("π", () => push("π"))}
        {btn("√", () => push("√("))}
        {["7","8","9","/"].map(v => btn(v, () => push(v)))}
        {["4","5","6","*"].map(v => btn(v, () => push(v)))}
        {["1","2","3","-"].map(v => btn(v, () => push(v)))}
        {btn("0", () => push("0"))}
        {btn(".", () => push("."))}
        {btn("+", () => push("+"))}
        {btn("=", evalIt, "bg-primary text-primary-foreground hover:bg-primary/90")}
      </div>
    </div>
  );
}

// export confetti helper so Result page uses the same lib
export function celebrate() {
  const end = Date.now() + 600;
  const colors = ["#2563EB", "#F97316", "#4F46E5", "#10B981"];
  (function frame() {
    confetti({ particleCount: 3, angle: 60, spread: 55, origin: { x: 0 }, colors });
    confetti({ particleCount: 3, angle: 120, spread: 55, origin: { x: 1 }, colors });
    if (Date.now() < end) requestAnimationFrame(frame);
  })();
}
