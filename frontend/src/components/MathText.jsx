import "katex/dist/katex.min.css";
import { InlineMath, BlockMath } from "react-katex";

// Renders a string that may contain LaTeX delimited by $...$, $$...$$, \(...\) or \[...\].
// Falls back to plain text when there is no math, so it is safe to use everywhere.
export default function MathText({ children, className = "", block = false }) {
  const text = children == null ? "" : String(children);
  if (!text) return null;

  // Normalise \( \) and \[ \] to $ and $$ so we have a single split token
  const normalised = text
    .replace(/\\\[(.+?)\\\]/gs, (_, m) => `$$${m}$$`)
    .replace(/\\\((.+?)\\\)/gs, (_, m) => `$${m}$`);

  if (!normalised.includes("$")) {
    return <span data-testid="math-text" className={className}>{text}</span>;
  }

  // Split on $$...$$ first then $...$
  const parts = normalised.split(/(\$\$[^$]+\$\$|\$[^$]+\$)/g);
  return (
    <span data-testid="math-text" className={className}>
      {parts.map((p, i) => {
        try {
          if (p.startsWith("$$") && p.endsWith("$$")) {
            return <BlockMath key={i} math={p.slice(2, -2)} />;
          }
          if (p.startsWith("$") && p.endsWith("$")) {
            const expr = p.slice(1, -1);
            return block ? <BlockMath key={i} math={expr} /> : <InlineMath key={i} math={expr} />;
          }
        } catch {
          return <span key={i}>{p}</span>;
        }
        return <span key={i}>{p}</span>;
      })}
    </span>
  );
}
