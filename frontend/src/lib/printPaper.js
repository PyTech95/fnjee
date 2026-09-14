// Opens a clean printable question paper in a new window (Print → Save as PDF).
const OPT = ["A", "B", "C", "D", "E", "F"];

export function printPaper({ title, duration, questions = [], institution = "Abhyash Mantra", withAnswers = false }) {
  const totalMarks = questions.reduce((a, q) => a + (Number(q.marks) || 4), 0);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const body = questions.map((q, i) => {
    const opts = (q.options || []).map((o, j) => `<div class="opt">(${OPT[j]}) ${esc(o)}</div>`).join("");
    const ans = withAnswers && q.correct ? `<div class="ans"><b>Answer:</b> ${esc((q.correct || []).join(", "))}</div>` : "";
    return `<div class="q"><div class="qt"><b>Q${i + 1}.</b> ${esc(q.text)} <span class="m">[${q.marks || 4}]</span></div><div class="opts">${opts}</div>${ans}</div>`;
  }).join("");

  const html = `<!doctype html><html><head><meta charset="utf-8"><title>${esc(title)}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <style>
    body{font-family:Georgia,'Times New Roman',serif;max-width:800px;margin:24px auto;padding:0 24px;color:#111;line-height:1.5}
    .hd{text-align:center;border-bottom:2px solid #111;padding-bottom:10px;margin-bottom:16px}
    .hd h1{margin:0;font-size:22px;letter-spacing:.5px}
    .meta{display:flex;justify-content:space-between;font-size:14px;margin:10px 0 20px}
    .q{margin:0 0 16px;page-break-inside:avoid}
    .qt{font-size:15px}.m{color:#555;font-size:12px}
    .opts{margin:6px 0 0 22px;display:grid;grid-template-columns:1fr 1fr;gap:2px 24px}
    .opt{font-size:14px}.ans{margin-top:4px;color:#0a7d34;font-size:13px}
    .foot{text-align:center;margin-top:24px;border-top:1px solid #999;padding-top:8px;font-size:12px;color:#666}
    @media print{button{display:none}}
  </style></head><body>
  <div class="hd"><h1>${esc(institution)}</h1><div style="font-size:16px;margin-top:4px">${esc(title)}</div></div>
  <div class="meta"><span>Time: ${esc(duration)} Minutes</span><span>Maximum Marks: ${totalMarks}</span></div>
  ${body}
  <div class="foot">— END OF PAPER —</div>
  <div style="text-align:center;margin-top:16px"><button onclick="window.print()">Print / Save as PDF</button></div>
  </body></html>`;

  const w = window.open("", "_blank");
  if (!w) return;
  w.document.open(); w.document.write(html); w.document.close();
}
