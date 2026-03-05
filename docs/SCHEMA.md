# Fantasy Football Monte Carlo Draft Helper
## Module 1 — Data Schema & Validation Rules

This document defines the CSV schema, data constraints, and validation rules enforced by the Data Loader.

---

# 1. CSV Schema

### File format
- UTF-8 encoded CSV
- Must include a header row
- Header must match **exactly**:

```text
Name,Position,Mean,StdDev
```


### Column Definitions

#### Name
- Type: `string`
- Required
- Trimmed before validation
- Must be non-empty after trimming
- Must not contain unescaped commas (otherwise the row will have an incorrect column count)

#### Position
- Type: `string`
- Required
- Case-insensitive; loader will automatically uppercase
- Allowed values:
  - `QB`
  - `RB`
  - `WR`
  - `TE`

#### Mean
- Type: `float`
- Required
- Represents **expected weekly fantasy points**
- Must parse as a real number
- Range: **0 ≤ Mean ≤ 60**
- Must **not** be `NaN` or `Infinity`

#### StdDev
- Type: `float`
- Required
- Represents **weekly volatility of fantasy points**
- Must parse as a real number
- Range: **0 ≤ StdDev ≤ 25**
- Must **not** be `NaN` or `Infinity`

---

# 2. Auto-Fix Rules (Safe Normalization)

The loader should:

- Trim whitespace on all fields
- Uppercase `Position`
- Collapse multiple internal spaces in `Name` (optional but recommended)

The loader should **not** attempt unsafe corrections such as:

- Guessing numeric values
- Replacing missing fields
- Fixing malformed CSV structure

---

# 3. Validation Rules Checklist

### A. File & Header
- [ ] Header must match exactly: `Name,Position,Mean,StdDev`
- [ ] Each row must contain **exactly 4 columns**

### B. Field Validation

**Name**
- [ ] Not empty after trimming
- [ ] No unescaped commas causing extra columns

**Position**
- [ ] Must be one of `{QB, RB, WR, TE}`

**Mean**
- [ ] Must parse as numeric
- [ ] Range **0–60 inclusive**
- [ ] Must not be `NaN` or `Infinity`

**StdDev**
- [ ] Must parse as numeric
- [ ] Range **0–25 inclusive**
- [ ] Must not be `NaN` or `Infinity`

---

### C. Row-level Validations

- [ ] Reject rows with missing fields
- [ ] Reject rows with invalid numeric values
- [ ] Reject rows with unknown positions
- [ ] Reject rows with extra or missing columns

---

### D. Duplicate Handling Policy

For rows where `Name` and `Position` match an earlier row:

- **Keep the first occurrence**
- **Reject all later duplicates**
- Emit a **warning or error message** for each rejected duplicate

---

# 4. Error Message Format

Each error should include:

- **Line number** (1-based, including header)
- **Reason**
- **Field name(s) involved**
- **Offending value** (when appropriate)

### Examples

```text
Line 7: Invalid Position 'K' (allowed: QB,RB,WR,TE)
Line 5: Mean is non-numeric 'twelve'
Line 3: Negative StdDev '-2.0'
Line 9: Duplicate player (Name='Gabe Repeat', Position='QB')
Line 12: Column count 5 (expected 4)
```


---

This schema is stable for the MVP and supports predictable, testable parsing for the CLI-based Monte Carlo simulation engine.