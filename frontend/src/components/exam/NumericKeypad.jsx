import { Delete } from "lucide-react";
import { sanitizeNumericInput, normalizeValidation } from "@/lib/numericValidation";

// The ONE canonical on-screen numeric keypad for the CBT module.
// Controlled component: value is always a string; onChange receives a string.
export default function NumericKeypad({ value = "", onChange, validation }) {
  const v = normalizeValidation(validation);

  const apply = (next) => {
    const sanitized = sanitizeNumericInput(value, next, v);
    onChange(sanitized);
  };

  const pressDigit = (d) => apply(value + d);
  const pressDot = () => {
    if (v.integerOnly || !v.allowDecimal) return;
    if (value.includes(".")) return;
    apply(value === "" || value === "-" ? value + "0." : value + ".");
  };
  const pressSign = () => {
    if (!v.allowNegative) return;
    apply(value.startsWith("-") ? value.slice(1) : "-" + value);
  };
  const backspace = () => onChange(value.slice(0, -1));
  const clearAll = () => onChange("");

  const Key = ({ label, onClick, testid, className = "", disabled = false }) => (
    <button
      type="button"
      data-testid={testid}
      onClick={onClick}
      disabled={disabled}
      className={`h-12 rounded-md border border-slate-300 bg-white text-lg font-semibold text-slate-800 hover:bg-slate-100 active:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors ${className}`}
    >
      {label}
    </button>
  );

  return (
    <div data-testid="numeric-keypad" className="w-full max-w-xs select-none">
      <div className="grid grid-cols-3 gap-2">
        {["7", "8", "9", "4", "5", "6", "1", "2", "3"].map((d) => (
          <Key key={d} label={d} testid={`keypad-${d}`} onClick={() => pressDigit(d)} />
        ))}
        <Key
          label="."
          testid="keypad-dot"
          onClick={pressDot}
          disabled={v.integerOnly || !v.allowDecimal}
        />
        <Key label="0" testid="keypad-0" onClick={() => pressDigit("0")} />
        <Key
          label="+/−"
          testid="keypad-sign"
          onClick={pressSign}
          disabled={!v.allowNegative}
        />
      </div>
      <div className="grid grid-cols-2 gap-2 mt-2">
        <Key
          label={
            <span className="inline-flex items-center gap-1.5">
              <Delete className="h-4 w-4" /> Backspace
            </span>
          }
          testid="keypad-backspace"
          onClick={backspace}
          className="text-sm"
        />
        <Key
          label="Clear All"
          testid="keypad-clear"
          onClick={clearAll}
          className="text-sm text-red-600 border-red-200 hover:bg-red-50"
        />
      </div>
    </div>
  );
}
