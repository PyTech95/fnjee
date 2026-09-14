// Static content for exam pages, cities and blog.
export const EXAM_PAGES = {
  jee: {
    slug: "jee",
    name: "JEE Main & Advanced",
    short: "JEE",
    tagline: "Real exam simulation for JEE Main & Advanced.",
    heroHeadline: "JEE Main & Advanced Online Test Series — Real Exam Simulation",
    heroSub: "AI-powered CBT mock tests that match the actual JEE paper pattern — with chapter-wise practice, PYQs, All India rank, and detailed analytics.",
    hook: "For Class 11–12 aspirants, droppers and Kota-style repeaters.",
    subjects: ["Physics", "Chemistry", "Mathematics"],
    stats: [
      { label: "PYQ questions", value: "50,000+" },
      { label: "Full mocks", value: "120+" },
      { label: "Chapter tests", value: "1,200+" },
      { label: "Avg. accuracy lift", value: "+18%" },
    ],
    features: [
      { title: "JEE-identical CBT interface", body: "Same look, timer, palette, and section navigation as the actual JEE Main paper — build muscle memory before test day." },
      { title: "Chapter, part & full mocks", body: "Baby tests (30Q), part tests (60Q), and full-length mocks (75Q, 3 hr) so you can layer difficulty gradually." },
      { title: "Previous Year Question bank", body: "10 years of Main + Advanced PYQs, tagged by chapter, difficulty, and concept — perfect for last-mile revision." },
      { title: "All India rank estimate", body: "Every mock reveals your predicted rank vs the current cohort so you know exactly where you stand." },
      { title: "Weak topic auto-drill", body: "AI spots the 3 concepts costing you the most marks and generates a targeted 15-min drill." },
      { title: "Reattempt & solutions library", body: "Retake any mock, watch solution walkthroughs, and bookmark for last-week revision." },
    ],
    faqs: [
      { q: "Is the CBT interface exactly like NTA JEE?", a: "Yes — same palette, mark-for-review, section switch, auto-submit and timer behavior. Students report zero interface surprise on exam day." },
      { q: "Do you cover JEE Advanced multi-correct and integer types?", a: "Absolutely — single-correct, multi-correct MCQ, integer, and paragraph-based questions are all supported." },
      { q: "How often are new mocks added?", a: "New full mocks every week during Jan–May cycle, plus 5+ chapter tests every day." },
    ],
    cta: "Start free JEE mock",
  },
  neet: {
    slug: "neet",
    name: "NEET UG",
    short: "NEET",
    tagline: "NCERT-based CBT practice that actually moves your rank.",
    heroHeadline: "NEET Online Test Series & NCERT-Based CBT Mock Tests",
    heroSub: "Daily NCERT MCQ practice, chapter-wise tests, full-length mocks, and AI-powered weak-topic drills — everything a NEET aspirant needs in one place.",
    hook: "Class 11–12, droppers, Biology, Physics & Chemistry aligned to NCERT line-by-line.",
    subjects: ["Physics", "Chemistry", "Biology (Botany + Zoology)"],
    stats: [
      { label: "NCERT-tagged MCQs", value: "1,20,000+" },
      { label: "Full mocks", value: "80+" },
      { label: "Chapter tests", value: "900+" },
      { label: "Daily streaks", value: "Unlocked" },
    ],
    features: [
      { title: "NCERT-line MCQs", body: "Every biology question tagged to the exact NCERT line — because that's where 85% of NEET Biology comes from." },
      { title: "Daily DPP + streaks", body: "Daily Practice Problems keep you sharp — miss a day and lose your streak, exactly what a NEET rank demands." },
      { title: "NTA-identical CBT engine", body: "Real palette, real timer, real section switch — walk into the AIIMS/NEET center on autopilot." },
      { title: "Chapter-wise & subject-wise tests", body: "Filter by chapter, topic, or difficulty. Weak in Human Physiology? Drill it in one click." },
      { title: "Rank predictor after every mock", body: "Compare your score against 1 lakh+ aspirants and see your projected AIR — updated after every attempt." },
      { title: "Custom test generator", body: "Pick subjects + chapters + count and generate your own paper. Perfect for the 30-min lunch-break revision." },
    ],
    faqs: [
      { q: "Are your NEET mocks NCERT-based?", a: "Yes — every MCQ is line-tagged to the NCERT source, especially in Biology where 80%+ of NEET questions come directly from NCERT sentences." },
      { q: "Do you offer subject-wise tests?", a: "Yes — Botany, Zoology, Physics and Chemistry, each broken down by chapter and topic." },
      { q: "Is there a free trial?", a: "Yes — sign up for free and take unlimited full-length mocks in the trial period." },
    ],
    cta: "Start free NEET mock",
  },
  olympiads: {
    slug: "olympiads",
    name: "Olympiads & Scholarship Exams",
    short: "Olympiads",
    tagline: "NTSE, KVPY-alt, NSO, IMO, NSTSE and more.",
    heroHeadline: "Olympiad & Scholarship Exam Online Practice",
    heroSub: "Sharpen concepts with CBT practice for NTSE, NSO, IMO, NSTSE, IEO and school-level scholarship exams.",
    hook: "Class 6–12 students prepping for national talent search & Olympiads.",
    subjects: ["Mathematics", "Science", "Reasoning", "English"],
    stats: [
      { label: "Olympiad papers", value: "200+" },
      { label: "Sample tests", value: "600+" },
      { label: "Difficulty levels", value: "3-tier" },
      { label: "Explanations", value: "100%" },
    ],
    features: [
      { title: "Exam-specific patterns", body: "Papers modeled on each specific Olympiad — NTSE MAT/SAT, NSO section splits, IMO logical reasoning weightage." },
      { title: "Progressive difficulty", body: "Baby → Intermediate → Champion tests so students grow from school-level to Olympiad-level in weeks." },
      { title: "Reasoning + aptitude drills", body: "Standalone reasoning modules for NTSE, KVPY-style aptitude, and general knowledge." },
      { title: "Class-wise question mapping", body: "Every question tagged to class (6–12) so students see only what's appropriate to their level." },
    ],
    faqs: [
      { q: "Which Olympiads do you cover?", a: "NTSE, NSO, IMO, NSTSE, IEO, IOEL, and popular school-level scholarship tests." },
      { q: "Can primary students use it too?", a: "Yes — we have Class 6 onwards, with age-appropriate questions and playful test palettes." },
    ],
    cta: "Explore Olympiad tests",
  },
  "govt-exams": {
    slug: "govt-exams",
    name: "Govt & Other Exams",
    short: "Govt Exams",
    tagline: "SSC, Banking, Railways, State-PSC — one CBT platform.",
    heroHeadline: "Govt Job Exam Online Test Series",
    heroSub: "SSC CGL/CHSL, Banking (IBPS/SBI), Railways, State PSC — get real-CBT experience with sectional & full mocks.",
    hook: "For graduates prepping for competitive govt sector recruitment.",
    subjects: ["Quant Aptitude", "Reasoning", "English", "General Awareness"],
    stats: [
      { label: "Exams covered", value: "40+" },
      { label: "Question bank", value: "2,00,000+" },
      { label: "PYQs", value: "10 years" },
      { label: "Sectional tests", value: "Unlimited" },
    ],
    features: [
      { title: "SSC/IBPS/RRB layouts", body: "Each mock rendered in the exact interface used by the respective conducting body." },
      { title: "Sectional timing", body: "Practice with sectional time limits so you never over-invest on one section on the real day." },
      { title: "General Awareness updates", body: "Current affairs refreshed weekly — never walk in with stale GK." },
      { title: "Speed-vs-accuracy report", body: "See exactly which section is stealing your marks and drill it in isolation." },
    ],
    faqs: [
      { q: "Do you cover state PSCs?", a: "Yes — BPSC, UPPSC, MPPSC, HPSC and more state exams, with regional-language options rolling out." },
      { q: "Are your PYQs current?", a: "Yes — we ship the latest year's PYQ within 30 days of any major exam." },
    ],
    cta: "Explore Govt exam tests",
  },
};

export const CITIES = [
  { slug: "delhi", name: "Delhi NCR", state: "Delhi", tagline: "Kota-style test discipline from your Delhi home." },
  { slug: "kota", name: "Kota", state: "Rajasthan", tagline: "Extend your Kota classroom with CBT tests every night." },
  { slug: "patna", name: "Patna", state: "Bihar", tagline: "Bihar's toppers train on Abhyash Mantra — you should too." },
  { slug: "lucknow", name: "Lucknow", state: "Uttar Pradesh", tagline: "The UP JEE/NEET cohort's daily practice partner." },
  { slug: "jaipur", name: "Jaipur", state: "Rajasthan", tagline: "Pink City aspirants deserve pink-slip ranks." },
  { slug: "hyderabad", name: "Hyderabad", state: "Telangana", tagline: "South zone rankers train with our IIT-JEE mocks." },
  { slug: "mumbai", name: "Mumbai", state: "Maharashtra", tagline: "Between local trains — build your rank on your phone." },
  { slug: "kolkata", name: "Kolkata", state: "West Bengal", tagline: "Bengal's medical aspirants swear by our NEET series." },
  { slug: "chennai", name: "Chennai", state: "Tamil Nadu", tagline: "TN JEE/NEET aspirants find their edge here." },
  { slug: "bengaluru", name: "Bengaluru", state: "Karnataka", tagline: "Karnataka's engineering hopefuls calibrate their prep here." },
  { slug: "ahmedabad", name: "Ahmedabad", state: "Gujarat", tagline: "Gujarat's ambitious learners practice smarter with AI." },
  { slug: "pune", name: "Pune", state: "Maharashtra", tagline: "MHT-CET, JEE, NEET — the Pune all-rounder's home." },
];

export const BLOG_POSTS = [
  {
    slug: "neet-2027-strategy",
    title: "NEET 2027 Strategy: How Daily NCERT MCQs Beat 6-Month Cramming",
    tag: "NEET",
    date: "2026-01-28",
    read: "6 min read",
    excerpt: "Why toppers trust a slow, disciplined daily-MCQ approach over the last-3-month sprint — and how to build the habit.",
    body: `The single biggest predictor of a top-1000 NEET rank isn't IQ or coaching cost — it's whether the student did daily NCERT-line MCQ practice for 12+ months.

**The 80/20 of NEET Biology**
Roughly 80% of NEET Biology questions are direct lifts from NCERT sentences. If you drill NCERT line-by-line MCQs every single day, you compound accuracy at a rate cramming can never match.

**Your daily 45-minute routine**
- 10 min: Yesterday's wrong questions
- 20 min: New chapter MCQs (20–25 questions)
- 10 min: One short mock or sectional test
- 5 min: Review + mark for revision

Do that for a year and your Biology accuracy naturally lands in the 90%+ zone. Physics and Chemistry follow the same daily-drill logic — just with heavier problem-solving.

**Pair it with weekly full mocks**
Every Sunday, take a full 3h 20min mock in one sitting. That's how you build stamina — the invisible skill that separates rank 500 from rank 5000.

Start free on Abhyash Mantra and lock in your daily streak today.`,
  },
  {
    slug: "jee-main-cbt-interface-tips",
    title: "JEE Main CBT Interface: 7 Tips That Save You 15 Marks",
    tag: "JEE",
    date: "2026-01-22",
    read: "5 min read",
    excerpt: "Small interface habits — palette color codes, mark-for-review discipline, section switch shortcuts — that quietly protect your rank.",
    body: `Every JEE Main year, thousands of well-prepared students lose 10–20 marks not to concepts but to CBT interface mistakes. Here are the 7 habits that fix that.

**1. Read the palette color code before you start**
Green = answered, purple = marked for review, red = seen but not answered. Know these cold — you'll save 60 seconds per section on exam day.

**2. Never mark-for-review AND answer**
Marking a solved question keeps you second-guessing. Answer, move on, don't look back.

**3. Use section-switch strategically**
Chemistry usually has the fastest solve time. Do Chem first to lock in easy marks and warm up your brain.

**4. Save 5 minutes at the end for palette review**
Sweep the palette for stragglers — one dropped Q can be 4 marks.

**5. Ignore the fastest guy in the hall**
The kid clicking rapidly in the corner is almost never the topper. Stay in your own tempo.

**6. Practice on the exact CBT layout**
This is the whole point of Abhyash Mantra — our JEE interface is pixel-identical to NTA's.

**7. Deep-breath at every section switch**
30 seconds. Every switch. Physiologically resets your prefrontal cortex.

Rehearse these in every mock and they become automatic by exam day.`,
  },
  {
    slug: "chapter-wise-vs-full-mocks",
    title: "Chapter-Wise Tests vs Full Mocks — Which Should You Prioritize?",
    tag: "Strategy",
    date: "2026-01-15",
    read: "4 min read",
    excerpt: "The 70/20/10 rule that top coaching institutes use to balance micro-drills, part tests, and full mocks.",
    body: `Both matter — but not equally, and not at the same time.

**Phase 1 (Foundation, 6+ months out): 70% chapter-wise**
Focus on chapter-wise tests. Master one chapter, then the next. Full mocks at this stage just demoralize you.

**Phase 2 (Consolidation, 3–6 months out): 50/50**
Half chapter-wise, half sectional/part tests. Start layering subjects together.

**Phase 3 (Rank push, final 3 months): 70% full mocks**
Now full mocks dominate. Chapter-wise only for weak spots the mocks reveal.

**The 10% rule**
In every phase, keep 10% of your practice for PYQs — they're the ground truth of what actually gets asked.

On Abhyash Mantra, use the Custom Test Generator to blend chapter-wise + PYQs in one click.`,
  },
];

export const TESTIMONIALS = [
  { name: "Aditi R.", role: "NEET AIR 412", city: "Kota", quote: "The daily NCERT MCQ streak on Abhyash Mantra is literally why I stayed disciplined for 14 months." },
  { name: "Karan M.", role: "JEE Main 99.4 %ile", city: "Delhi", quote: "The CBT interface was identical to what NTA showed us. Zero surprises on exam day." },
  { name: "Sana P.", role: "NEET UG rank 1,832", city: "Hyderabad", quote: "The rank predictor kept me honest. Every Sunday mock told me where I really stood." },
  { name: "Rohit K.", role: "JEE Advanced qualifier", city: "Patna", quote: "The weak-topic auto-drill saved my Organic Chemistry. Went from 40% to 78% in six weeks." },
];
