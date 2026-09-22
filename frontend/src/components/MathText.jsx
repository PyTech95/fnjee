import { Children, useId } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { InlineFormula } from "./InlineFormula";
import "./question-content.css";

const mathChildren = (items) => Children.map(items, item => typeof item === "string" ? <InlineFormula>{item}</InlineFormula> : item);

export default function MathText({ children, className = "", block = false, testId }) {
  const uid = useId().replace(/:/g, "");
  const id = testId || `math-text-${uid}`;
  const text = children == null ? "" : String(children);
  if (!text) return null;
  if (!/\n\s*\|?\s*:?-{3,}:?\s*\|/.test(text)) {
    return <InlineFormula testId={id} className={className} block={block}>{text}</InlineFormula>;
  }
  return <div data-testid={id} className={`question-rich-text ${className}`}>
    <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml components={{
      table: ({ children, node }) => <div className="question-table-wrap"><table data-testid={`${id}-table-${node.position.start.line}`}>{children}</table></div>,
      th: ({ children }) => <th scope="col">{mathChildren(children)}</th>,
      td: ({ children }) => <td>{mathChildren(children)}</td>,
      p: ({ children }) => <p>{mathChildren(children)}</p>,
      a: ({ children }) => <span>{children}</span>,
      img: () => null,
    }}>{text}</ReactMarkdown>
  </div>;
}