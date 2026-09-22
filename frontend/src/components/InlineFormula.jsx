import { useId } from "react";
import { InlineMath, BlockMath } from "react-katex";
import "katex/dist/katex.min.css";

export const InlineFormula = ({ children, className = "", block = false, testId }) => {
  const uid = useId().replace(/:/g, "");
  const text = children == null ? "" : String(children);
  if (!text) return null;
  const normalised = text.replace(/\\\[(.+?)\\\]/gs, (_, m) => `$$${m}$$`).replace(/\\\((.+?)\\\)/gs, (_, m) => `$${m}$`);
  const parts = normalised.split(/(\$\$[^$]+\$\$|\$[^$]+\$)/g);
  return <span data-testid={testId || `formula-${uid}`} className={`whitespace-pre-wrap break-words ${className}`}>
    {parts.map((p,i) => {
      if (p.startsWith("$$") && p.endsWith("$$")) return <BlockMath key={i} math={p.slice(2,-2)} />;
      if (p.startsWith("$") && p.endsWith("$")) return block ? <BlockMath key={i} math={p.slice(1,-1)} /> : <InlineMath key={i} math={p.slice(1,-1)} />;
      return <span key={i}>{p}</span>;
    })}
  </span>;
};