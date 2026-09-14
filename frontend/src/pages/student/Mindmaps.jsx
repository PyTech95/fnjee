import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { Network, ChevronRight, Download } from "lucide-react";

const HUE = { Biology: "142 60% 42%", Physics: "221 83% 53%", Chemistry: "24 95% 53%", Mathematics: "271 60% 55%" };

export default function Mindmaps() {
  const [maps, setMaps] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    api.get("/mindmaps").then((r) => {
      setMaps(r.data);
      if (r.data.length) setSelected(r.data[0]);
    });
  }, []);

  return (
    <div data-testid="student-mindmaps-page" className="space-y-8">
      <div>
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Connect ideas</div>
        <h1 className="font-display font-bold text-3xl sm:text-4xl tracking-tight mt-1">Mindmaps · one sheet per chapter</h1>
        <p className="text-muted-foreground mt-2 max-w-2xl">
          A single page linking every formula and concept in a chapter. Perfect for last-mile revision.
        </p>
      </div>

      <div className="grid lg:grid-cols-[280px,1fr] gap-6">
        <Card className="en-card p-4 h-fit">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground px-2 pt-2 pb-3">All chapters</div>
          <div className="space-y-1">
            {maps.map((m) => {
              const active = selected?.id === m.id;
              return (
                <button key={m.id} onClick={() => setSelected(m)}
                  data-testid={`mindmap-item-${m.chapter.toLowerCase().replace(/\s+/g, "-")}`}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors duration-200 ${
                    active ? "bg-primary/10 text-primary" : "hover:bg-muted"
                  }`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className={`font-medium ${active ? "text-primary" : ""}`}>{m.chapter}</div>
                      <div className="text-xs text-muted-foreground">{m.subject}</div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </button>
              );
            })}
          </div>
        </Card>

        {selected && (
          <Card data-testid="mindmap-canvas" className="en-card p-6 lg:p-8 relative overflow-hidden">
            <div className="flex items-center justify-between mb-6">
              <div>
                <Badge variant="secondary" className="rounded-full">{selected.subject}</Badge>
                <h2 className="font-display font-bold text-2xl mt-2">{selected.chapter}</h2>
              </div>
              <Button variant="outline" className="rounded-full" data-testid="mindmap-download">
                <Download className="h-4 w-4 mr-1.5" /> A4 PDF
              </Button>
            </div>

            <div className="rounded-2xl border border-border bg-gradient-to-br from-muted/30 to-transparent p-8 lg:p-12">
              <div className="grid place-items-center">
                <div className="relative w-full max-w-3xl">
                  <div className="mx-auto w-fit rounded-full px-6 py-3 font-display font-bold text-lg text-white shadow-lg"
                    style={{ background: `hsl(${HUE[selected.subject] || HUE.Biology})` }}>
                    {selected.root}
                  </div>

                  <div className="mt-10 grid sm:grid-cols-2 gap-6">
                    {selected.branches.map((b, i) => (
                      <div key={b.name} className="relative">
                        <div className="rounded-2xl border-2 border-dashed p-4 bg-card"
                          style={{ borderColor: `hsl(${HUE[selected.subject] || HUE.Biology} / 0.4)` }}>
                          <div className="flex items-center gap-2">
                            <div className="h-8 w-8 rounded-lg grid place-items-center text-white text-xs font-bold"
                              style={{ background: `hsl(${HUE[selected.subject] || HUE.Biology})` }}>
                              {String.fromCharCode(65 + i)}
                            </div>
                            <div className="font-display font-semibold">{b.name}</div>
                          </div>
                          <ul className="mt-3 space-y-1.5 text-sm">
                            {b.leaves.map((leaf) => (
                              <li key={leaf} className="flex items-start gap-2 pl-1">
                                <span className="h-1.5 w-1.5 rounded-full mt-1.5 shrink-0" style={{ background: `hsl(${HUE[selected.subject] || HUE.Biology})` }} />
                                <span className="text-foreground/80">{leaf}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 text-xs text-muted-foreground flex items-center gap-2">
              <Network className="h-4 w-4" /> Every formula & concept in this chapter, connected. Print on A4 for revision.
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
