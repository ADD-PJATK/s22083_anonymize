"""
Local Data Anonymizer
Replaces sensitive strings in .txt / .md / .csv / .json files
using a JSON mapping file. Standard library only.
"""

import argparse
import json
import os
import re
import sys

SUPPORTED_EXTENSIONS = {".json", ".txt", ".md", ".csv"}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Anonymize sensitive strings in a text file using a JSON mapping.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python anonymize.py --mapping examples/mapping.json "
            "--input examples/sample.csv --output out/sample.anon.csv\n"
            "  python anonymize.py --mapping examples/mapping.json "
            "--input examples/note.md --dry-run"
        ),
    )
    parser.add_argument("--mapping", required=True, metavar="FILE",
                        help="path to JSON mapping file")
    parser.add_argument("--input", required=True, metavar="FILE",
                        help="path to source file (.txt, .md, .csv, .json)")
    parser.add_argument("--output", metavar="FILE",
                        help="path for the anonymized output file (required unless --dry-run)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print replacement counts per rule without writing any file")
    args = parser.parse_args()

    if not args.dry_run and args.output is None:
        parser.error("--output is required unless --dry-run is specified")

    return args


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def read_utf8(path, label="file"):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        sys.exit(f"Error: {label} not found: {path}")
    except UnicodeDecodeError as exc:
        sys.exit(f"Error: {label} '{path}' contains invalid UTF-8: {exc}")
    except OSError as exc:
        sys.exit(f"Error: cannot read {label} '{path}': {exc}")


def write_utf8(path, text):
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError as exc:
        sys.exit(f"Error: cannot write output file '{path}': {exc}")


# ---------------------------------------------------------------------------
# Mapping loading and validation
# ---------------------------------------------------------------------------

def load_mapping(path):
    raw = read_utf8(path, "mapping file")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.exit(f"Error: mapping file is not valid JSON: {exc}")
    return data


def validate_mapping(data):
    """Validate mapping structure and return (replacements, case_sensitive)."""
    if not isinstance(data, dict):
        sys.exit("Error: mapping file must be a JSON object.")

    if "replacements" not in data:
        sys.exit("Error: mapping file must contain a 'replacements' key.")

    replacements = data["replacements"]
    if not isinstance(replacements, list):
        sys.exit("Error: 'replacements' must be a JSON array.")

    for idx, rule in enumerate(replacements):
        loc = f"replacements[{idx}]"
        if not isinstance(rule, dict):
            sys.exit(f"Error: {loc} must be a JSON object.")

        if "find" not in rule:
            sys.exit(f"Error: {loc} is missing required key 'find'.")
        find = rule["find"]
        if not isinstance(find, list):
            sys.exit(f"Error: {loc}.find must be a JSON array.")
        if len(find) == 0:
            sys.exit(f"Error: {loc}.find must contain at least one string.")
        for j, entry in enumerate(find):
            if not isinstance(entry, str):
                sys.exit(f"Error: {loc}.find[{j}] must be a string.")
            if entry == "":
                sys.exit(f"Error: {loc}.find[{j}] must not be an empty string.")

        if "replace" not in rule:
            sys.exit(f"Error: {loc} is missing required key 'replace'.")
        if not isinstance(rule["replace"], str):
            sys.exit(f"Error: {loc}.replace must be a string.")

    options = data.get("options", {})
    if not isinstance(options, dict):
        sys.exit("Error: 'options' must be a JSON object.")

    case_sensitive = options.get("case_sensitive", False)
    if not isinstance(case_sensitive, bool):
        sys.exit("Error: options.case_sensitive must be a boolean (true or false).")

    return replacements, case_sensitive


# ---------------------------------------------------------------------------
# Replacement engine
# ---------------------------------------------------------------------------

def apply_replacements(text, replacements, case_sensitive):
    """
    Apply all rules to text in order.

    Returns:
        (result_text, counts) where counts[i][j] is the number of
        replacements made by find[j] of rule i.

    Algorithm:
        Rules are applied sequentially; within each rule, find entries are
        applied in array order. Each find entry triggers a single left-to-right
        scan that replaces all non-overlapping occurrences (earliest match wins).
        The replacement token is never re-scanned, so earlier rules and earlier
        find entries always win over later ones.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    counts = []

    for rule in replacements:
        replace_token = rule["replace"]
        rule_counts = []
        for find_str in rule["find"]:
            pattern = re.escape(find_str)
            occurrences = re.findall(pattern, text, flags=flags)
            count = len(occurrences)
            rule_counts.append(count)
            if count:
                text = re.sub(pattern, lambda _m, tok=replace_token: tok, text, flags=flags)
        counts.append(rule_counts)

    return text, counts


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def ensure_parent_dir(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except OSError as exc:
            sys.exit(f"Error: cannot create output directory '{parent}': {exc}")


def print_dry_run_report(replacements, counts):
    total = sum(c for rule_counts in counts for c in rule_counts)
    print("Dry run — no file written.")
    print(f"Total replacements: {total}")
    for i, (rule, rule_counts) in enumerate(zip(replacements, counts)):
        rule_total = sum(rule_counts)
        print(f"  Rule {i} (-> {rule['replace']!r}): {rule_total} replacement(s)")
        for j, (find_str, count) in enumerate(zip(rule["find"], rule_counts)):
            print(f"    find[{j}] {find_str!r}: {count}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # Validate input extension
    _, ext = os.path.splitext(args.input)
    if ext.lower() not in SUPPORTED_EXTENSIONS:
        sys.exit(
            f"Error: unsupported file extension '{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # Load and validate mapping
    mapping_data = load_mapping(args.mapping)
    replacements, case_sensitive = validate_mapping(mapping_data)

    # Load input file
    text = read_utf8(args.input, "input file")

    # Apply replacements
    result_text, counts = apply_replacements(text, replacements, case_sensitive)

    if args.dry_run:
        print_dry_run_report(replacements, counts)
        return

    # Warn when input and output are the same file
    input_abs = os.path.abspath(args.input)
    output_abs = os.path.abspath(args.output)
    if input_abs == output_abs:
        print(
            f"Warning: --output is the same path as --input. "
            f"The original file will be overwritten.",
            file=sys.stderr,
        )

    ensure_parent_dir(args.output)
    write_utf8(args.output, result_text)

    total = sum(c for rule_counts in counts for c in rule_counts)
    print(f"Done. Output written to: {args.output} ({total} replacement(s) made.)")


if __name__ == "__main__":
    main()
