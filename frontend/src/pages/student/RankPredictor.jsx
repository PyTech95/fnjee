import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { api } from "@/lib/api";
import { Trophy, Target, TrendingUp } from "lucide-react";

export default function RankPredictor() {
  const [score, setScore] = useState(600);
  const [target, setTarget] = useState("NEET");
  const [total, setTotal] = useState(720);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  const predict = async () => {
    setBusy(true);
    try {
      const r = await api.post("/rank-predictor", { score, total, target });
      setResult(r.data);
    } finally { setBusy(false); }
  };

  return (
    <div data-testid="student-rank-predictor-page" className="space-y-8">
      <div>
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Predict your rank</div>
        <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">All India Rank predictor</h1>
        <p className="text-muted-foreground mt-2 max-w-2xl">
          Enter your expected score. We map you to the college band based on the current cohort trajectory.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card data-testid="rank-configurator" className="en-card p-6 lg:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="h-11 w-11 rounded-xl bg-primary/10 text-primary grid place-items-center"><Target className="h-5 w-5" /></div>
            <div>
              <div className="font-display font-semibold text-lg">Your projection</div>
              <div className="text-sm text-muted-foreground">Move the slider to change your projected score.</div>
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <Label className="text-sm font-semibold">Exam</Label>
              <div className="mt-3 flex gap-2">
                {["NEET", "JEE Main", "JEE Advanced"].map((t) => (
                  <button key={t} onClick={() => { setTarget(t); setTotal(t === "NEET" ? 720 : t === "JEE Main" ? 300 : 360); }}
                    data-testid={`rank-target-${t.toLowerCase().replace(/\s+/g, "-")}`}
                    className={`px-4 py-2 rounded-full text-sm border transition-colors duration-200 ${
                      target === t ? "bg-primary text-primary-foreground border-primary" : "border-border hover:border-primary/40"
                    }`}>{t}</button>
                ))}
              </div>
            </div>

            <div>
              <div className="flex justify-between items-baseline">
                <Label className="text-sm font-semibold">Projected score</Label>
                <div>
                  <span className="font-display font-bold text-4xl text-primary">{score}</span>
                  <span className="text-lg text-muted-foreground"> / {total}</span>
                </div>
              </div>
              <Slider data-testid="rank-score-slider" min={0} max={total} step={5} value={[score]}
                onValueChange={(v) => setScore(v[0])} className="mt-4" />
              <div className="mt-2 text-xs text-muted-foreground">
                {Math.round((score / total) * 100)}% · Percentile bucket determines your college band.
              </div>
            </div>

            <div>
              <Label className="text-sm font-semibold">Total marks</Label>
              <Input data-testid="rank-total-input" type="number" value={total} onChange={(e) => setTotal(+e.target.value || 720)} className="rounded-full mt-2 max-w-[160px]" />
            </div>

            <Button data-testid="predict-rank-btn" size="lg" onClick={predict} disabled={busy} className="rounded-full">
              {busy ? "Predicting…" : "Predict my rank"}
            </Button>
          </div>
        </Card>

        <Card data-testid="rank-result" className="en-card p-6 lg:p-8 relative overflow-hidden">
          <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-primary/10 blur-2xl" aria-hidden />
          <div className="relative">
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Result</div>
            {result ? (
              <>
                <div className="mt-3 flex items-center gap-3">
                  <div className="h-14 w-14 rounded-2xl bg-accent/15 text-accent grid place-items-center"><Trophy className="h-7 w-7" /></div>
                  <div>
                    <div className="text-xs text-muted-foreground uppercase tracking-wider">Projected AIR</div>
                    <div className="font-display font-bold text-4xl">
                      {result.predicted_rank_low.toLocaleString()}
                      <span className="text-muted-foreground text-2xl"> – {result.predicted_rank_high.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
                <Badge className="mt-4 rounded-full bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20">
                  Band · {result.band}
                </Badge>
                <div className="mt-6 grid grid-cols-3 gap-3">
                  <Stat label="Score" value={result.score} />
                  <Stat label="%age" value={`${result.percentage}%`} />
                  <Stat label="Cohort" value={result.cohort_size.toLocaleString()} />
                </div>
                <p className="text-sm text-muted-foreground mt-6 leading-relaxed">{result.message}</p>
                <div className="mt-6 p-4 rounded-xl border border-dashed border-primary/40 bg-primary/5 text-sm">
                  <div className="flex items-center gap-2 font-semibold"><TrendingUp className="h-4 w-4 text-primary" /> Push it further</div>
                  <div className="text-muted-foreground mt-1">Every 10 marks moves you one tier — daily DPP + Sunday full mocks is the shortest route.</div>
                </div>
              </>
            ) : (
              <div className="mt-6 text-sm text-muted-foreground">Move the slider and press <b>Predict my rank</b> to see your projected AIR band.</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="p-3 rounded-xl border border-border bg-card">
      <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className="font-display font-bold text-lg mt-0.5">{value}</div>
    </div>
  );
}
