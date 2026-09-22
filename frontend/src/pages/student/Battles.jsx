import { useEffect, useRef, useState, useCallback } from "react";
import { battleApi } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Swords, Users, Trophy, Copy, Clock, CheckCircle2, XCircle, Crown, Loader2, Plus, LogIn } from "lucide-react";
import MathText from "@/components/MathText";
import { QuestionContent } from "@/components/QuestionContent";
import { toast } from "sonner";

const LETTERS = ["A", "B", "C", "D", "E", "F"];
const SUBJECTS = ["Physics", "Chemistry", "Biology", "Mathematics"];

export default function Battles() {
  const { user } = useAuth();
  const [roomId, setRoomId] = useState(null);
  const [room, setRoom] = useState(null);
  const [subject, setSubject] = useState("Physics");
  const [num, setNum] = useState(5);
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [sel, setSel] = useState(null);
  const [fb, setFb] = useState(null);
  const answeredIndex = useRef(-1);

  const poll = useCallback(async () => {
    if (!roomId) return;
    try {
      const s = await battleApi.state(roomId);
      setRoom(s);
      if (s.status === "active" && s.index !== answeredIndex.current && (fb || sel != null)) {
        // new question arrived
      }
    } catch { /* keep last */ }
  }, [roomId, fb, sel]);

  useEffect(() => {
    if (!roomId) return;
    poll();
    const t = setInterval(poll, 1500);
    return () => clearInterval(t);
  }, [roomId, poll]);

  // reset selection when the active question index changes
  useEffect(() => {
    if (room?.status === "active" && room.index !== answeredIndex.current) {
      setSel(null); setFb(null);
    }
  }, [room?.index, room?.status]);

  const create = async () => {
    setBusy(true);
    try { const r = await battleApi.create({ subject, num_questions: Number(num) || 5 }); setRoomId(r.id); setRoom(r); }
    catch (e) { toast.error(e?.response?.data?.detail || "Could not create room"); } finally { setBusy(false); }
  };
  const join = async () => {
    if (!code.trim()) return;
    setBusy(true);
    try { const r = await battleApi.join({ code: code.trim() }); setRoomId(r.id); setRoom(r); }
    catch (e) { toast.error(e?.response?.data?.detail || "Could not join"); } finally { setBusy(false); }
  };
  const startBattle = async () => {
    try { const r = await battleApi.start(roomId); setRoom(r); } catch (e) { toast.error(e?.response?.data?.detail || "Could not start"); }
  };
  const answer = async (i) => {
    if (fb || room.already_answered) return;
    setSel(i); answeredIndex.current = room.index;
    try {
      const res = await battleApi.answer(roomId, { index: room.index, selected: [LETTERS[i]] });
      setFb(res);
      if (res.correct) toast.success(`+${res.points} pts!`); 
    } catch (e) { toast.error(e?.response?.data?.detail || "Too late!"); }
  };
  const leave = () => { setRoomId(null); setRoom(null); setSel(null); setFb(null); answeredIndex.current = -1; };
  const copyCode = () => { navigator.clipboard?.writeText(room.code); toast.success("Code copied"); };

  // ---- Landing (no room) ----
  if (!room) {
    return (
      <div data-testid="battles-page" className="space-y-6 max-w-3xl">
        <Header />
        <div className="grid sm:grid-cols-2 gap-5">
          <Card className="en-card p-6 space-y-4">
            <div className="flex items-center gap-2 font-display font-semibold"><Plus className="h-4 w-4 text-primary" /> Create a battle</div>
            <Select value={subject} onValueChange={setSubject}>
              <SelectTrigger data-testid="battle-subject"><SelectValue /></SelectTrigger>
              <SelectContent>{SUBJECTS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
            </Select>
            <div>
              <div className="text-sm font-medium mb-1">Questions</div>
              <Input data-testid="battle-num" type="number" min={3} max={15} value={num} onChange={(e) => setNum(e.target.value)} />
            </div>
            <Button data-testid="battle-create" className="rounded-full w-full" onClick={create} disabled={busy}>
              {busy ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Swords className="h-4 w-4 mr-2" />} Create room
            </Button>
          </Card>
          <Card className="en-card p-6 space-y-4">
            <div className="flex items-center gap-2 font-display font-semibold"><LogIn className="h-4 w-4 text-primary" /> Join with a code</div>
            <Input data-testid="battle-code" value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} placeholder="e.g. 4XPMN" className="uppercase tracking-widest font-mono text-lg" maxLength={5} />
            <Button data-testid="battle-join" variant="outline" className="rounded-full w-full" onClick={join} disabled={busy || !code.trim()}>Join battle</Button>
          </Card>
        </div>
      </div>
    );
  }

  // ---- Lobby ----
  if (room.status === "lobby") {
    const isHost = room.host_id === user?.id;
    return (
      <div data-testid="battle-lobby" className="space-y-6 max-w-3xl">
        <Header />
        <Card className="en-card p-6 text-center">
          <div className="text-xs uppercase tracking-widest text-muted-foreground">Share this code</div>
          <button onClick={copyCode} data-testid="battle-room-code" className="inline-flex items-center gap-3 mt-2 font-display font-bold text-5xl tracking-[0.2em] hover:text-primary transition-colors">
            {room.code} <Copy className="h-5 w-5" />
          </button>
          <div className="text-sm text-muted-foreground mt-2">{room.subject} · {room.num_questions} questions</div>
        </Card>
        <Card className="en-card p-6">
          <div className="flex items-center gap-2 mb-4 font-display font-semibold"><Users className="h-4 w-4" /> Players ({room.players.length})</div>
          <div className="space-y-2">
            {room.players.map((p) => (
              <div key={p.user_id} className="flex items-center gap-3 p-3 rounded-xl bg-muted/40" data-testid={`lobby-player-${p.user_id}`}>
                <div className="h-8 w-8 rounded-lg bg-primary/10 text-primary grid place-items-center font-bold text-sm">{p.name.slice(0, 2).toUpperCase()}</div>
                <span className="font-medium text-sm">{p.name}{p.user_id === user?.id && " (You)"}</span>
                {p.user_id === room.host_id && <Badge variant="secondary" className="rounded-full ml-auto">Host</Badge>}
              </div>
            ))}
          </div>
          <div className="mt-5 flex gap-2">
            {isHost ? (
              <Button data-testid="battle-start" className="rounded-full" onClick={startBattle} disabled={room.players.length < 1}>Start battle</Button>
            ) : (
              <div className="text-sm text-muted-foreground flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Waiting for host to start…</div>
            )}
            <Button variant="ghost" className="rounded-full" onClick={leave}>Leave</Button>
          </div>
        </Card>
      </div>
    );
  }

  // ---- Finished ----
  if (room.status === "finished") {
    const winner = room.players[0];
    return (
      <div data-testid="battle-result" className="space-y-6 max-w-2xl">
        <Header />
        <Card className="en-card p-8 text-center">
          <Crown className="h-10 w-10 text-amber-500 mx-auto" />
          <div className="font-display font-bold text-2xl mt-2">{winner?.name} wins! 🏆</div>
          <div className="text-muted-foreground text-sm">{winner?.score} points</div>
        </Card>
        <Card className="en-card p-6">
          <div className="font-display font-semibold mb-4">Final ranking</div>
          <div className="space-y-2">
            {room.players.map((p) => (
              <div key={p.user_id} className={`flex items-center justify-between p-3 rounded-xl ${p.user_id === user?.id ? "bg-primary/10 ring-1 ring-primary/30" : "bg-muted/40"}`} data-testid={`result-player-${p.rank}`}>
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg grid place-items-center font-display font-bold text-sm bg-background border border-border">#{p.rank}</div>
                  <span className="font-medium text-sm">{p.name}{p.user_id === user?.id && " · You"}</span>
                </div>
                <Badge className="rounded-full tabular-nums">{p.score} pts</Badge>
              </div>
            ))}
          </div>
          <Button className="rounded-full mt-5" onClick={leave}>Back to battles</Button>
        </Card>
      </div>
    );
  }

  // ---- Active ----
  const q = room.question;
  const locked = fb || room.already_answered;
  return (
    <div data-testid="battle-active" className="space-y-5 max-w-4xl">
      <div className="flex items-center justify-between">
        <Badge variant="secondary" className="rounded-full">Q{(room.index ?? 0) + 1} / {room.num_questions}</Badge>
        <div className={`flex items-center gap-1.5 font-display font-bold text-xl tabular-nums ${room.time_left <= 5 ? "text-rose-600" : "text-primary"}`} data-testid="battle-timer">
          <Clock className="h-5 w-5" /> {room.time_left ?? 0}s
        </div>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div className="h-full bg-primary transition-all duration-1000 ease-linear" style={{ width: `${((room.time_left ?? 0) / (room.per_q_seconds || 20)) * 100}%` }} />
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        <Card className="en-card p-6 lg:col-span-2" data-testid="battle-question">
          {q ? (
            <>
              <QuestionContent question={q} testId="battle-question" className="text-base font-medium leading-relaxed" />
              <div className="mt-4 space-y-2">
                {(q.options || []).map((opt, i) => {
                  const isSel = sel === i;
                  const isCorrect = fb && fb.correct_answer?.map((x) => x.toUpperCase()).includes(LETTERS[i]);
                  const showWrong = fb && isSel && !fb.correct;
                  return (
                    <button key={i} data-testid={`battle-opt-${i}`} disabled={locked} onClick={() => answer(i)}
                      className={`w-full text-left p-3 rounded-xl border flex items-center gap-3 transition-colors ${
                        fb ? (isCorrect ? "border-emerald-500 bg-emerald-500/10" : showWrong ? "border-rose-500 bg-rose-500/10" : "border-border opacity-70")
                        : isSel ? "border-primary bg-primary/10" : "border-border hover:bg-muted"}`}>
                      <span className={`h-6 w-6 rounded-full grid place-items-center text-xs font-bold shrink-0 ${isSel ? "bg-primary text-primary-foreground" : "border border-border"}`}>{LETTERS[i]}</span>
                      <span className="flex-1"><MathText>{String(opt)}</MathText></span>
                      {fb && isCorrect && <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
                      {showWrong && <XCircle className="h-4 w-4 text-rose-600" />}
                    </button>
                  );
                })}
              </div>
              {locked && <div className="mt-3 text-sm text-muted-foreground">{fb ? (fb.correct ? `Nice! +${fb.points} pts` : "Locked in — waiting for next question…") : "Answer locked."}</div>}
            </>
          ) : <div className="text-sm text-muted-foreground">Loading question…</div>}
        </Card>

        <Card className="en-card p-5" data-testid="battle-live-scores">
          <div className="flex items-center gap-2 mb-3 font-display font-semibold text-sm"><Trophy className="h-4 w-4 text-primary" /> Live scores</div>
          <div className="space-y-2">
            {room.players.map((p) => (
              <div key={p.user_id} className={`flex items-center justify-between p-2.5 rounded-lg text-sm ${p.user_id === user?.id ? "bg-primary/10" : "bg-muted/40"}`}>
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-xs font-bold text-muted-foreground w-4">#{p.rank}</span>
                  <span className="truncate">{p.name}{p.user_id === user?.id && " (You)"}</span>
                </div>
                <span className="font-bold tabular-nums shrink-0">{p.score}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

function Header() {
  return (
    <div>
      <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary flex items-center gap-2">
        <Swords className="h-3.5 w-3.5" /> Quiz Battles
      </div>
      <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">Challenge your classmates</h1>
      <p className="text-muted-foreground mt-1">Real-time multiplayer quiz rooms with a shared countdown. Fastest correct answer wins the most points.</p>
    </div>
  );
}
