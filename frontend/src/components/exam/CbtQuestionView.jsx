import MathText from "@/components/MathText";
import { QuestionImage } from "@/components/QuestionContent";
import NumericKeypad from "@/components/exam/NumericKeypad";
import { sanitizeNumericInput } from "@/lib/numericValidation";

const LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H"];

// Shared question renderer used by BOTH the student CBT exam and the admin
// live preview, so the admin sees exactly what the candidate sees.
// `value` is an array of answer strings (option ids, or ["<numeric>"]).
export function CbtQuestionView({ question, lang = "en", value = [], onChange, readOnly = false, showMeta = true, testIdPrefix = "cbv" }) {
  if (!question) return null;
  const text = lang === "hi" ? (question.hi?.text || question.en?.text) : question.en?.text;
  const tid = (s) => `${testIdPrefix}-${s}`;

  const toggleOption = (optId) => {
    if (readOnly || !onChange) return;
    if (question.type === "scm") onChange([optId]);
    else onChange(value.includes(optId) ? value.filter((x) => x !== optId) : [...value, optId]);
  };

  return (
    <div className="cbt-question-view">
      {showMeta && (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs mb-3">
          <span className="uppercase tracking-wide px-2 py-0.5 rounded bg-slate-100 text-slate-600" data-testid={tid("type")}>
            {question.type === "scm" ? "Single Correct" : question.type === "msq" ? "Multiple Correct" : "Numerical"}
          </span>
          <span className="text-green-700 font-medium">+{question.marks}</span>
          <span className="text-red-600 font-medium">-{question.negative_marks}</span>
        </div>
      )}

      <div className="text-base leading-relaxed" data-testid={tid("question-text")}>
        <MathText>{text}</MathText>
      </div>
      {question.image_url && <QuestionImage src={question.image_url} alt={question.image_alt} testId={tid("question-image")} />}

      <div className="mt-5">
        {(question.type === "scm" || question.type === "msq") && (
          <div className="space-y-2.5" data-testid={tid("options")}>
            {(question.options || []).map((opt, i) => {
              const sel = value.includes(opt.id);
              return (
                <label key={opt.id} data-testid={tid(`option-${LETTERS[i]}`)}
                  className={`flex items-start gap-3 p-3 rounded border ${readOnly ? "cursor-default" : "cursor-pointer"} transition-colors ${sel ? "border-blue-600 bg-blue-50" : "border-slate-300 bg-white"}`}>
                  <input
                    type={question.type === "scm" ? "radio" : "checkbox"}
                    name={`cbv-${question.id || "q"}`}
                    checked={sel}
                    disabled={readOnly}
                    onChange={() => toggleOption(opt.id)}
                    data-testid={tid(`option-input-${LETTERS[i]}`)}
                    className="mt-1 h-4 w-4 accent-blue-600"
                  />
                  <span className="font-semibold text-slate-700 w-5">{LETTERS[i]}.</span>
                  <span className="flex-1"><MathText>{lang === "hi" ? opt.hi : opt.en}</MathText></span>
                </label>
              );
            })}
          </div>
        )}

        {question.type === "numerical" && (
          <div data-testid={tid("numerical")} className="space-y-4">
            <div>
              <label className="block text-xs uppercase tracking-widest text-slate-500 mb-1">Your Answer</label>
              <input
                data-testid={tid("numerical-input")}
                value={value[0] || ""}
                readOnly={readOnly}
                onChange={(e) => {
                  if (readOnly || !onChange) return;
                  onChange([sanitizeNumericInput(value[0] || "", e.target.value, question.numerical_validation)]);
                }}
                inputMode="decimal"
                className="w-full max-w-xs h-12 px-3 rounded border border-slate-300 text-xl font-mono focus:border-blue-600 focus:outline-none disabled:bg-slate-50"
                placeholder="Type or use keypad"
              />
            </div>
            {!readOnly && (
              <NumericKeypad value={value[0] || ""} onChange={(v) => onChange([v])} validation={question.numerical_validation} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Build the normalized CBT question shape from a raw stored question doc
// (used by the admin preview so it renders with the same pipeline).
export function toCbtQuestionShape(q) {
  if (!q) return null;
  const t = (q.type || "mcq_single").toLowerCase();
  const type = t === "mcq_multi" ? "msq" : (["integer", "numerical", "decimal", "numeric"].includes(t) ? "numerical" : "scm");
  const rawOpts = (q.options && q.options.length ? q.options : (q.type === "true_false" ? ["True", "False"] : []));
  const options = rawOpts.map((text, i) => ({ id: `opt_${i}`, en: text, hi: (q.options_hi && q.options_hi[i]) || text }));
  return {
    id: q.id,
    type,
    marks: q.marks ?? 4,
    negative_marks: q.negative_marks ?? 1,
    en: { text: q.text || "" },
    hi: { text: q.text_hi || q.text || "" },
    image_url: q.image_url || null,
    image_alt: q.image_alt || "Question diagram",
    options,
    numerical_validation: q.numerical_validation || (type === "numerical" ? { integerOnly: q.type === "integer", allowDecimal: q.type !== "integer", allowNegative: true, maxDecimalPlaces: 4, maxLength: 12 } : null),
  };
}
