import { useEffect, useState } from "react";
import { podcastsApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Headphones, Play, Pause, Sparkles } from "lucide-react";
import { toast } from "sonner";

export default function Podcasts() {
  const [chapters, setChapters] = useState([]);
  const [active, setActive] = useState(null);      // {subject, chapter, script}
  const [loading, setLoading] = useState(false);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    podcastsApi.chapters().then(setChapters);
    return () => { try { window.speechSynthesis?.cancel(); } catch {} };
  }, []);

  const generateAndPlay = async (c) => {
    setLoading(true); setActive(null);
    try {
      const r = await podcastsApi.script(c.subject, c.chapter);
      setActive({ ...c, script: r.script, used_ai: r.used_ai });
      speak(r.script);
    } catch { toast.error("Could not generate podcast"); }
    finally { setLoading(false); }
  };

  const speak = (text) => {
    if (!("speechSynthesis" in window)) { toast.error("Voice not supported"); return; }
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.0; u.pitch = 1.0; u.lang = "en-IN";
    u.onstart = () => setPlaying(true);
    u.onend = () => setPlaying(false);
    u.onerror = () => { setPlaying(false); toast.error("Voice unavailable"); };
    setPlaying(true);
    window.speechSynthesis.speak(u);
  };

  const toggle = () => {
    if (playing) { window.speechSynthesis.cancel(); setPlaying(false); }
    else if (active?.script) speak(active.script);
  };

  return (
    <div data-testid="podcasts-page" className="space-y-8">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary flex items-center gap-2">
            <Headphones className="h-3.5 w-3.5" /> Audio · AI-narrated
          </div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-2">Chapter Podcasts</h1>
          <p className="text-muted-foreground mt-1">3-minute AI summaries — for the bus, gym, or lunch break.</p>
        </div>
      </div>

      {active && (
        <Card data-testid="active-podcast" className="en-card p-6 relative overflow-hidden">
          <div className="absolute -right-8 -top-8 h-40 w-40 rounded-full bg-primary/10 blur-3xl" aria-hidden />
          <div className="relative flex items-center gap-4">
            <button data-testid="play-toggle" onClick={toggle} className={`h-14 w-14 rounded-full grid place-items-center ${playing ? "bg-accent text-accent-foreground" : "bg-primary text-primary-foreground"}`}>
              {playing ? <Pause className="h-6 w-6" /> : <Play className="h-6 w-6 ml-0.5" />}
            </button>
            <div className="flex-1 min-w-0">
              <div className="text-xs text-muted-foreground uppercase tracking-widest flex items-center gap-2">{active.subject} · Chapter Podcast {active.used_ai && <Sparkles className="h-3 w-3 text-primary" />}</div>
              <div className="font-display font-semibold text-lg truncate">{active.chapter}</div>
              <div className="text-xs text-muted-foreground">{playing ? "Playing…" : "Paused — tap play to resume"}</div>
            </div>
          </div>
          <div className="mt-4 p-4 rounded-xl bg-muted/40 text-sm max-h-48 overflow-y-auto en-scroll whitespace-pre-wrap">{active.script}</div>
        </Card>
      )}

      <div>
        <h2 className="font-display font-semibold text-lg mb-3">Pick a chapter</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {chapters.map((c, i) => (
            <Card key={i} data-testid={`podcast-card-${i}`} className="en-card p-4 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <Badge variant="secondary" className="rounded-full text-[10px] mb-1">{c.subject}</Badge>
                <div className="font-semibold truncate">{c.chapter}</div>
                <div className="text-xs text-muted-foreground">{c.questions} practice questions</div>
              </div>
              <Button size="icon" variant="outline" className="rounded-full shrink-0" onClick={() => generateAndPlay(c)} disabled={loading}>
                <Play className="h-4 w-4" />
              </Button>
            </Card>
          ))}
          {chapters.length === 0 && <div className="text-sm text-muted-foreground">No chapters yet. Ask admin to add questions with chapter tags.</div>}
          {loading && <div className="text-sm text-muted-foreground">Generating your podcast with AI…</div>}
        </div>
      </div>
    </div>
  );
}
