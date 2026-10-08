// Single canonical numeric-answer validation utility for the CBT module.
// Keeps the answer as a STRING at all times. "0" is a valid answer; "" is empty.
// Allows transient edit states like "-" or "." while typing, but these are NOT
// treated as a final, savable answer.

export const DEFAULT_NUMERIC_VALIDATION = {
  integerOnly: false,
  allowDecimal: true,
  allowNegative: true,
  maxDecimalPlaces: 4,
  maxLength: 12,
};

export function normalizeValidation(v) {
  return { ...DEFAULT_NUMERIC_VALIDATION, ...(v || {}) };
}

// Returns the next string value if the edit is allowed, else returns the
// previous value unchanged. `next` is the full candidate string after an edit.
export function sanitizeNumericInput(prev, next, validation) {
  const v = normalizeValidation(validation);
  if (next === "") return "";

  // Only permitted characters.
  const allowedChars = v.integerOnly ? /^[-0-9]*$/ : /^[-0-9.]*$/;
  if (!allowedChars.test(next)) return prev;

  // Minus sign: only allowed at position 0, and only when negatives are allowed.
  const minusCount = (next.match(/-/g) || []).length;
  if (minusCount > 1) return prev;
  if (minusCount === 1 && (!v.allowNegative || next.indexOf("-") !== 0)) return prev;

  // Decimal point rules.
  if (!v.integerOnly && v.allowDecimal) {
    const dotCount = (next.match(/\./g) || []).length;
    if (dotCount > 1) return prev;
    if (dotCount === 1) {
      const decimals = next.split(".")[1] || "";
      if (decimals.length > v.maxDecimalPlaces) return prev;
    }
  }

  // Length guard (excludes nothing special; counts the whole string).
  if (next.length > v.maxLength) return prev;

  return next;
}

// A value that is a complete, savable number (not a transient edit state).
export function isFinalNumericValue(value) {
  if (value === "" || value == null) return false;
  const s = String(value);
  if (s === "-" || s === "." || s === "-." || s === "+") return false;
  // must parse to a real number
  return !Number.isNaN(Number(s));
}
