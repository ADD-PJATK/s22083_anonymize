# Local Data Anonymizer

A local CLI tool that reads a JSON mapping file and anonymizes `.json`, `.txt`, `.md`, and `.csv` files by replacing sensitive strings with placeholder tokens. All files are treated as plain UTF-8 text. The tool writes an anonymized copy to a specified output path.

The program does not call any HTTP APIs, cloud services, or AI services. All replacements are performed locally using static rules from the mapping file.

---

## Prerequisites

- Python **3.10** or newer
- No external packages — standard library only

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

| Argument    | Required | Description                                             |
|-------------|----------|---------------------------------------------------------|
| `--mapping` | Yes      | Path to the JSON mapping file                           |
| `--input`   | Yes      | Path to the source file to anonymize                    |
| `--output`  | Yes      | Path where the anonymized output file will be written   |
| `--dry-run` | No       | Print replacement counts per rule without writing a file |

### Examples

```bash
# Anonymize a Markdown file
python anonymize.py --mapping examples/mapping.json --input examples/note.md --output out/note.anon.md

# Anonymize a CSV file
python anonymize.py --mapping examples/mapping.json --input examples/sample.csv --output out/sample.anon.csv

# Anonymize a plain-text file
python anonymize.py --mapping examples/mapping.json --input examples/sample.txt --output out/sample.anon.txt

# Anonymize a JSON file
python anonymize.py --mapping examples/mapping.json --input examples/sample.json --output out/sample.anon.json

# Dry run — print how many replacements would be made, write nothing
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
    },
    {
      "find": ["123-456-789"],
      "replace": "PHONE_A"
    }
  ],
  "options": {
    "case_sensitive": false
  }
}
```

### Fields

**`replacements`** — required array of replacement rules, processed in the order listed.

Each rule contains:

- **`find`** — a non-empty JSON array of strings. Every string in the array is replaced by the same token. Must contain at least one non-empty string.
- **`replace`** — the anonymized token that is substituted for every match from `find`. Must be a non-empty string.

**`options.case_sensitive`** — optional boolean, defaults to `false`.

- `false` — matching is case-insensitive; `Anna`, `ANNA`, and `anna` are all matched.
- `true` — matching is case-sensitive; only the exact casing is matched.

### Validation

The program exits with a non-zero status and a readable error message if:

- `replacements` is missing or is not an array
- Any rule's `find` is missing, not an array, empty, or contains an empty string
- Any rule's `replace` is missing or is not a string
- `options.case_sensitive` is present but is not a boolean

---

## Matching and overlap policy

**Rule order:** rules are processed in the order listed in `replacements`. The output of rule *N* is passed as input to rule *N+1*.

**Find-entry order:** within one rule, each string in `find` is applied to the current text in array order.

**Left-to-right scan:** for each `find` entry, the tool performs a single left-to-right scan of the current text and replaces all non-overlapping occurrences. The earliest match wins.

**Replacements are applied immediately:** after a region is replaced, the cursor advances past the replacement token. The token is never re-scanned, so it cannot be matched again by the current or any later `find` entry.

**Overlap policy — earlier wins:** if two `find` entries could match overlapping regions, the one that appears earlier in the array is applied first. Because replacements are applied immediately, the later entry will see the already-substituted token rather than the original text. The same rule applies across rules: an earlier rule's replacement is never undone by a later rule.

**Default is case-insensitive** (`case_sensitive: false`). Original casing of the matched text is not preserved — the matched span is replaced entirely by the `replace` token.

---

## Supported file types

| Extension | Treatment                        |
|-----------|----------------------------------|
| `.txt`    | Read as UTF-8 text, apply replacements, write UTF-8 |
| `.md`     | Same as above                    |
| `.csv`    | Same as above                    |
| `.json`   | Same as above                    |

All formats are treated as plain UTF-8 text. No format-specific parsing is performed.

---

## Output behaviour

- The **output parent directory is created automatically** if it does not exist.
- The output file is written as **UTF-8**.
- If `--output` resolves to the same absolute path as `--input`, the tool prints a warning to stderr and overwrites the original. The operation is allowed because the user explicitly provided that path.
- If the input file contains invalid UTF-8, the program exits immediately with a readable error.

---

## Before and after example

**`examples/note.md` (before)**

```
# Contact note

Kontakt: A. Nowak <anna@firma.test>
Phone: 123-456-789
```

**After running**

```bash
python anonymize.py --mapping examples/mapping.json --input examples/note.md --output out/note.anon.md
```

**`out/note.anon.md` (after)**

```
# Contact note

Kontakt: PERSON_A <EMAIL_A>
Phone: PHONE_A
```

---

## Screenshots

Terminal screenshots proving successful runs on multiple file types are stored in the `screenshots/` folder.

---

## Academic integrity

This tool performs local, static string replacement based on rules loaded from a JSON file. It does not send any file contents or data to third parties, and does not use any AI or cloud services at runtime.
