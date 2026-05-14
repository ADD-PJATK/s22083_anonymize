# Local Data Anonymizer

A small, self-contained CLI tool that replaces sensitive strings in text-based files using a JSON mapping file. Runs entirely locally — no network access, no external dependencies, no AI services.

Supported input formats: `.txt`, `.md`, `.csv`, `.json`

---

## Prerequisites

- Python **3.8** or newer
- No third-party packages — standard library only

---

## Installation

```bash
git clone https://github.com/ADD-org/s22083_anonymize.git
cd s22083_anonymize
```

No virtual environment or `pip install` needed.

---

## Usage

```bash
python anonymize.py --mapping <mapping_file> --input <input_file> --output <output_file>
```

### Arguments

| Argument      | Required | Description |
|---------------|----------|-------------|
| `--mapping`   | Yes      | Path to the JSON mapping file (see format below) |
| `--input`     | Yes      | Path to the source file to anonymize |
| `--output`    | Yes      | Path where the anonymized file will be written |
| `--dry-run`   | No       | Print replacement counts per rule without writing any file |

### Command-line examples

```bash
# Anonymize a CSV file
python anonymize.py --mapping examples/mapping.json --input examples/sample.csv --output out/sample.anon.csv

# Anonymize a plain-text file
python anonymize.py --mapping examples/mapping.json --input examples/sample.txt --output out/sample.anon.txt

# Anonymize a Markdown file
python anonymize.py --mapping examples/mapping.json --input examples/note.md --output out/note.anon.md

# Anonymize a JSON file
python anonymize.py --mapping examples/mapping.json --input examples/sample.json --output out/sample.anon.json

# Dry run — show how many replacements would be made, write nothing
python anonymize.py --mapping examples/mapping.json --input examples/sample.csv --dry-run
```

---

## Mapping file format

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
  "options": {
    "case_sensitive": false
  }
}
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `replacements` | Yes | Ordered array of replacement rules |
| `replacements[].find` | Yes | Non-empty array of strings — every entry maps to the same token |
| `replacements[].replace` | Yes | The anonymized token substituted for every match |
| `options.case_sensitive` | No | `false` (default) for case-insensitive matching; `true` for exact-case |

### Validation errors

The program exits with a non-zero status and a readable message if:

- `replacements` is missing or not an array
- Any rule's `find` array is missing, empty, or contains an empty string
- Any rule's `replace` is missing or empty

---

## Replacement algorithm

### Rule order

Rules are processed **in the order listed** in `replacements`. The output of rule *N* becomes the input for rule *N+1*.

### Within a rule — find-entry order

Inside one rule, each string in `find` is applied to the running text **in array order**. For each entry the tool performs a single **left-to-right scan**: it finds all non-overlapping occurrences (earliest position wins), replaces them with the rule's `replace` token, and then moves on to the next `find` entry.

Replacement text is **never re-scanned**: after a region is replaced with a token such as `PERSON_A`, the cursor advances past that token, so neither the current `find` entry nor later entries can accidentally match inside an already-substituted token (provided your tokens do not contain target strings, which you should ensure when designing mapping files).

### Overlap policy

**Within one rule:** `find` entries are applied sequentially to the same buffer. If entry `"A. Nowak"` produces `"PERSON_A"` in a region that also partially overlapped with a hypothetical later entry, that later entry will not see the original text — it sees the substituted token. This is deterministic: the first `find` entry in array order wins.

**Between rules:** a later rule never re-opens text already replaced by an earlier rule (same cursor-advance guarantee). Design your `replace` tokens to be clearly distinct from any `find` strings.

**Case-insensitive mode (`case_sensitive: false`):** matching is case-insensitive; the matched span is replaced entirely by the `replace` token (original casing is lost).

---

## Output file behaviour

- The output directory **must already exist**; the tool does not create it.
- If `--output` resolves to the same path as `--input`, the program **exits with an error** — it never silently overwrites the source file.
- If `--output` points to a different existing file, it **will be overwritten** (the user explicitly chose that path).

---

## Encoding

All files are read and written in **UTF-8**. If the input file contains invalid UTF-8 sequences, the program exits immediately with a readable error message.

---

## Examples folder

| File | Description |
|------|-------------|
| `examples/mapping.json` | Sample mapping with a person name (two aliases), an e-mail, and a phone number |
| `examples/note.md` | Short Markdown note containing the sensitive values |
| `examples/sample.txt` | Plain-text support ticket with the same sensitive values |
| `examples/sample.csv` | CSV contact list containing the sensitive values |
| `examples/sample.json` | JSON ticket object containing the sensitive values |

Run any of the commands in the [Usage](#usage) section against these files to see the tool in action.
