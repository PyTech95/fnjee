import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { duelsApi } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Swords, Trophy, ChevronRight, Copy } from "lucide-react";
import { toast } from "sonner";

export default function DuelChallenge() {
  const { code } = useParams();
  const { user, loading } = useAuth();
  const nav = useNavigate();
  const [duel, setDuel] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    duelsApi.get(code).then(setDuel).catch(() => setErr("Duel not found"));
  }, [code]);

  const accept = () => {
    if (!user) { localStorage.setItem("pending_duel", code); nav("/signup"); return; }
    if (user.role !== "student") { toast.error("Only students can accept duels"); return; }
    // reserve for after test complete
    localStorage.setItem("active_duel", code);
    nav(`/student/exam/${duel.test_id}`);
  };

  if (err) return <div className="min-h-screen grid place-items-center px-6"><Card className="en-card p-8 max-w-md text-center"><div className="font-display font-semibold text-xl">Duel not found</div><Button className="rounded-full mt-4" onClick={() => nav("/")}>Home</Button></Card></div>;
  if (!duel || loading) return <div className="min-h-screen grid place-items-center text-muted-foreground">Loading duel…</div>;

  const pct = duel.challenger_total ? Math.round(duel.challenger_score / duel.challenger_total * 100) : 0;

  return (
    <div data-testid="duel-page" className="min-h-screen bg-background grid place-items-center p-6">
      <Card className="en-card p-8 max-w-lg w-full relative overflow-hidden">
        <div className="absolute -right-16 -top-16 h-52 w-52 rounded-full bg-primary/15 blur-3xl" aria-hidden />
        <div className="relative">
          <div className="flex items-center gap-2 text-xs uppercase tracking-widest text-primary font-bold">
            <Swords className="h-3.5 w-3.5" /> You've been challenged
          </div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl mt-3 leading-tight">
            Beat {duel.challenger_name} on <span className="text-primary">{duel.test_title}</span>?
          </h1>
          <div className="mt-6 flex items-center gap-4 p-4 rounded-2xl bg-muted/50">
            <Avatar className="h-14 w-14"><AvatarFallback>{duel.challenger_name[0]}</AvatarFallback></Avatar>
            <div className="flex-1">
              <div className="text-xs text-muted-foreground uppercase tracking-widest">Their score</div>
              <div className="font-display font-bold text-2xl">{duel.challenger_score} <span className="text-base text-muted-foreground">/ {duel.challenger_total}</span></div>
              <div className="text-xs text-muted-foreground">{pct}% · beat this to win</div>
            </div>
            <Trophy className="h-8 w-8 text-accent" />
          </div>
          {duel.opponents?.length > 0 && (
            <div className="mt-4 space-y-1.5">
              <div className="text-xs uppercase tracking-widest text-muted-foreground">Already faced them</div>
              {duel.opponents.slice(0, 4).map((o, i) => (
                <div key={i} className="flex justify-between items-center text-sm p-2 rounded-lg bg-muted/40">
                  <span>{o.user_name}</span>
                  <Badge variant={o.score > duel.challenger_score ? "default" : "outline"} className="rounded-full">
                    {o.score} / {o.total} {o.score > duel.challenger_score && "🏆"}
                  </Badge>
                </div>
              ))}
            </div>
          )}
          <Button data-testid="accept-duel" onClick={accept} className="w-full rounded-full mt-6" size="lg">
            {user ? "Take the challenge" : "Sign up & take the challenge"} <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
          <p className="text-xs text-muted-foreground text-center mt-3">Free to join · Real CBT · Live rank compare</p>
        </div>
      </Card>
    </div>
  );
}
