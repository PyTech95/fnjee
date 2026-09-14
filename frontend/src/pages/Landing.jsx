import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Upload, Users, BarChart3, Award, Bell, ShieldCheck, Sparkles } from "lucide-react";

const FEATURES = [
  { icon: Upload, title: "Multi-format Import", body: "PageMaker, Word, Excel, PDF, Google Drive — AI-parsed into a review queue." },
  { icon: BookOpen, title: "Smart Question Bank", body: "Tag by subject, chapter, topic, difficulty. MCQ, integer, assertion-reason, subjective." },
  { icon: BarChart3, title: "Deep Analytics", body: "Chapter-wise heatmaps, speed vs accuracy, rank tracking across weeks." },
  { icon: Award, title: "Rewards & Referrals", body: "Streaks, coins wallet, leaderboards. Share & earn program built-in." },
  { icon: Users, title: "Parent Portal", body: "Parents see child progress, weak subjects, and assign supervised practice." },
  { icon: ShieldCheck, title: "Distraction-Free Exam", body: "Full-screen mode, question palette, timer, auto-submit — no more cheating." },
];

export default function Landing() {
  return (
    <div data-testid="landing-page" className="min-h-screen bg-background text-foreground">
      {/* header */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-background/70 border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-xl bg-primary text-primary-foreground grid place-items-center font-display font-bold">E</div>
            <span className="font-display font-bold text-xl tracking-tight">Abhyash Mantra</span>
          </div>
          <div className="flex items-center gap-2">
            <Link to="/login"><Button data-testid="header-login-btn" variant="ghost" className="rounded-full">Log in</Button></Link>
            <Link to="/signup"><Button data-testid="header-signup-btn" className="rounded-full">Get started</Button></Link>
          </div>
        </div>
      </header>

      {/* hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 en-grid-bg opacity-40" aria-hidden="true" />
        <div className="relative max-w-7xl mx-auto px-6 pt-20 pb-24 grid lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-7 en-fade-up">
            <Badge className="rounded-full mb-6 bg-secondary/15 text-secondary hover:bg-secondary/20 border border-secondary/30">
              <Sparkles className="h-3.5 w-3.5 mr-1.5" /> Built for JEE, NEET & Olympiads
            </Badge>
            <h1 className="font-display font-bold tracking-tight text-4xl sm:text-5xl lg:text-6xl leading-[1.05]">
              The exam platform<br/>coaching institutes<br/>
              <span className="text-primary">actually enjoy running.</span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground max-w-xl leading-relaxed">
              Upload your question paper in <b>PageMaker, Word, Excel, PDF or Google Drive</b> — Abhyash Mantra parses it,
              organises it, and turns it into timed mock tests with analytics. Three portals: Admin, Student, Parent.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/signup"><Button data-testid="hero-cta-signup" size="lg" className="rounded-full px-8">Start free</Button></Link>
              <Link to="/login"><Button data-testid="hero-cta-demo" size="lg" variant="outline" className="rounded-full px-8">Try demo login</Button></Link>
            </div>
            <div className="mt-10 flex gap-8 text-sm text-muted-foreground">
              <div><div className="font-display font-bold text-2xl text-foreground">4</div>Subjects covered</div>
              <div><div className="font-display font-bold text-2xl text-foreground">8</div>Question types</div>
              <div><div className="font-display font-bold text-2xl text-foreground">5+</div>Import formats</div>
            </div>
          </div>
          <div className="lg:col-span-5 en-fade-up" style={{animationDelay: "150ms"}}>
            <div className="relative">
              <img
                src="https://images.pexels.com/photos/16420237/pexels-photo-16420237.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
                alt="Student preparing for exams"
                className="rounded-3xl border border-border shadow-2xl object-cover w-full aspect-[4/5]"
              />
              <Card className="absolute -bottom-6 -left-6 p-4 w-64 shadow-xl border-border rounded-2xl">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-accent/15 text-accent grid place-items-center"><Bell className="h-5 w-5" /></div>
                  <div>
                    <div className="text-xs text-muted-foreground">Live insight</div>
                    <div className="font-semibold">Aarav improved 18% in Physics</div>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* features */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="max-w-2xl mb-12">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary mb-3">Everything in one nest</div>
          <h2 className="font-display font-bold text-3xl sm:text-4xl tracking-tight">Six modules. Zero switching.</h2>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f, i) => (
            <Card key={f.title} className="en-card p-6 en-fade-up" style={{animationDelay: `${i*60}ms`}} data-testid={`feature-${i}`}>
              <div className="h-11 w-11 rounded-xl bg-primary/10 text-primary grid place-items-center mb-4">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="font-display font-semibold text-lg mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.body}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* cta */}
      <section className="max-w-7xl mx-auto px-6 pb-24">
        <Card className="bg-primary text-primary-foreground p-10 lg:p-14 rounded-3xl border-0 relative overflow-hidden">
          <div className="absolute inset-0 en-grid-bg opacity-10" aria-hidden="true" />
          <div className="relative grid lg:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="font-display font-bold text-3xl sm:text-4xl tracking-tight leading-tight">Ready to run your first mock test?</h2>
              <p className="mt-4 text-primary-foreground/80 max-w-lg">Sign up your coaching institute today. Import questions in minutes, invite students, and go live.</p>
            </div>
            <div className="flex flex-wrap gap-3 lg:justify-end">
              <Link to="/signup"><Button data-testid="footer-cta-signup" size="lg" variant="secondary" className="rounded-full px-8">Create free account</Button></Link>
              <Link to="/login"><Button data-testid="footer-cta-login" size="lg" variant="outline" className="rounded-full px-8 border-primary-foreground/40 text-primary-foreground hover:bg-primary-foreground/10 hover:text-primary-foreground">Log in</Button></Link>
            </div>
          </div>
        </Card>
      </section>

      <footer className="border-t border-border">
        <div className="max-w-7xl mx-auto px-6 py-6 flex flex-wrap items-center justify-between gap-4 text-sm text-muted-foreground">
          <div>© 2026 Abhyash Mantra — Serious exam prep, joyfully delivered.</div>
          <div className="flex gap-4">
            <span>admin@examnest.io / Admin@123</span>
            <span>student1@examnest.io / Student@123</span>
            <span>parent1@examnest.io / Parent@123</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
