# Additional Assignment: Local Data Anonymizer (JSON / TXT / MD / CSV)

> **Estimated time:** ~45–60 minutes  
> **Tools allowed:** any editor or AI coding assistant — the solution itself must **not** call external APIs or any AI service.

---

## 1. Context

You will build a **small, self-contained program** that reads a **mapping file** (which values to hide and what to substitute) and a **target file** (one of: `.json`, `.txt`, `.md`, `.csv`), then writes an **anonymized copy** to disk.

Everything runs **locally**: no HTTP clients for anonymization, no cloud APIs, no large language models. Replacements are **deterministic** and based only on the mapping you load from JSON.

---

## 2. Problem statement

Sensitive strings (names, emails, phone numbers, addresses, IDs) often appear inside logs, exports, and hand-written documents saved as plain text or structured text (CSV, Markdown, JSON as text).

The goal is a **batch anonymization tool** that:

1. Loads **replacement rules** from a JSON configuration file.
2. Reads a **source file** in UTF-8 (format is still “text”; JSON/CSV/MD are not special-cased unless you document optional extras).
3. Applies substitutions and writes a **new output file** (never silently overwrite the original unless the user explicitly chooses the same path — document your behaviour).

---

## 3. Mapping file format (contract)

Your program must accept a mapping file with this **minimum** schema (you may add optional fields if you document them):

```json
{
  "replacements": [
    {
      "find": ["Jan Kowalski", "J. Kowalski", "KOWALSKI, Jan"],
      "replace": "PERSON_01"
    },
    {
      "find": ["jan.kowalski@example.com", "jkowalski@example.com"],
      "replace": "EMAIL_01"
    }
  ],
  "options": {
    "case_sensitive": false
  }
}
```

Rules:

- `replacements` is an array of **rules**. Each rule has:
  - **`find`**: a JSON **array of strings** — **many** alternative substrings that must all be replaced by the **same** token.
  - **`replace`**: a **single** string — the anonymized substitute for **every** match of **any** entry in that rule’s `find` list.
- Each `find` array must contain **at least one** non-empty string. Empty strings inside the array, an empty array, or a missing `replace` are invalid — your program should **exit with a clear error**.
- **Within one rule**, apply each string in `find` **in array order** (document whether you re-scan the whole file per `find` entry or merge passes — behaviour must be deterministic and described in the README).
- **`options.case_sensitive`**: when `false` (default if omitted), matching is case-insensitive; when `true`, matching is case-sensitive.
- **Order of rules**: process rules **in the order given** in `replacements` (after any sorting you document — if you sort, describe it in the README).
- **Overlapping matches**: document what happens if two different `find` strings overlap (e.g. `"ab"` vs `"bc"` in `"abc"`), including overlap **between** strings in the **same** rule. A simple acceptable policy is: *for each rule, for each `find` entry in order, scan left-to-right and replace* **or** *longest match among all active finds first* — pick one and describe it.

The **required** interoperable format is **`replacements` + `options`** as above (each rule: many `find`, one `replace`). Do not rely on undocumented shorthand formats for the graded submission.

---

## 4. Supported input file types

The tool must accept a source path whose extension is one of:

| Extension | Treatment |
|-----------|-----------|
| `.json` | Read as UTF-8 text, apply string replacements, write UTF-8 text. (You are **not** required to parse JSON into a tree unless you want to as an extra; plain text replacement is enough for the assignment.) |
| `.txt` | Same as above. |
| `.md` | Same as above. |
| `.csv` | Same as above. |

Encoding: **UTF-8** input and output. On invalid UTF-8, fail with a readable error.

---

## 5. Program interface (CLI)

Use any language. The interface must be usable from the terminal, for example:

```bash
python anonymize.py --mapping mapping.json --input data/sample.csv --output out/sample.anon.csv
```

or positional arguments — **document the exact invocation** in your README.

Required arguments / behaviour:

- **Mapping file** path (JSON as in section 3).
- **Input file** path (must exist).
- **Output file** path (parent directory may need to exist — document whether you create it).

Optional (nice to have, not required for full marks):

- `--dry-run` — print how many replacements would occur per rule or per `find` entry without writing.
- Verbose logging to stderr.

---

## 6. Explicit prohibitions

The submitted solution **must not**:

- Call **any** HTTP/HTTPS API to perform anonymization or “understand” the file.
- Use **any** LLM / AI cloud SDK (OpenAI, Anthropic, Google Generative AI, local inference HTTP, etc.) for masking or paraphrasing.
- Send file contents to a third party.

Static rules + local string processing only. Using AI **to help you write code** is fine; the **running program** must not depend on AI services.

---

## 7. Deliverables

Create a **new repository** in the ADD GitHub organisation:

- Repository name: `sXXXXX_anonymize` (your student ID, e.g. `s12345_anonymize`)
- Repository must be public (or accessible to the instructor)

The repository must contain:

- [ ] Source code for the **CLI anonymizer**
- [ ] Root `README.md` with: prerequisites, installation, **exact** command-line examples, explanation of mapping format and overlap policy
- [ ] Folder `examples/` with **at least**:
  - one `mapping.json` (valid per section 3),
  - one sample file per extension **or** fewer samples if you clearly show all four extensions in the README with copy-pasteable snippets
- [ ] `screenshots/` (or images embedded in README) showing a successful run (terminal + before/after or output file listing)
- [ ] `.gitignore` appropriate to your stack (e.g. `.env`, `__pycache__`, `node_modules`, `dist/`, IDE files)
- [ ] No secrets committed (if you use sample “secrets”, they must be fictional)

---

## 8. Grading (0–4 points)

| # | Criterion | Points |
|---|-----------|--------|
| 1 | Use repo form last week, named `sXXXXX_anonymize`, create new branch | 1 pt |
| 2 | README: prerequisites, install, run, mapping format, edge-case policy | 1 pt |
| 3 | Screenshots / artefacts proving a run on at least **two** different extensions among `.json`, `.txt`, `.md`, `.csv` | 1 pt |
| 4 | Git hygiene: ≥3 meaningful commits, sensible `.gitignore`, working `examples/` | 1 pt |

See `ACCEPTANCE.md` for the full checklist.

---

## 9. Minimal behavioural example

**`examples/mapping.json`**

```json
{
  "replacements": [
    {
      "find": ["Anna Nowak", "A. Nowak"],
      "replace": "PERSON_A"
    },
    {
      "find": ["anna@firma.test"],
      "replace": "EMAIL_A"
    }
  ],
  "options": { "case_sensitive": false }
}
```

**`examples/note.md` (before)**

```markdown
Kontakt: A. Nowak <anna@firma.test>
```

**After anonymization**

```markdown
Kontakt: PERSON_A <EMAIL_A>
```

Your implementation should produce the same logical outcome for this example (exact spacing may follow your documented rules).

---

## 10. Suggested self-test checklist (non-grading)

- [ ] Case-insensitive mode replaces `ANNA` / `Anna` consistently when `case_sensitive` is `false`.
- [ ] A rule with **several** strings in `find` all map to the **same** `replace` token.
- [ ] CSV with commas and quoted fields still round-trips as **text** (you are not required to parse CSV cells unless you want to).
- [ ] JSON file remains valid JSON **after** replacement if the input was valid JSON and replacements do not break structure (students should choose safe dummy tokens).

---

## 11. Academic integrity

Write your own small tool. Reusing a generic “find-replace” CLI **without** your own repository, README, examples, and documented mapping format is not sufficient — the deliverable is **your** documented anonymizer matching this specification.
