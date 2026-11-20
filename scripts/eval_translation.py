"""Translate the phrase set and print a Markdown quality report.

    python scripts/eval_translation.py [--phrases FILE] [--no-glossary] [--out report.md]

Needs the ``argos`` extra; downloads the required Argos models on first run.
"""

from __future__ import annotations

import argparse
import sys
import time
import tomllib
from collections import defaultdict
from pathlib import Path

from telsiz.glossary import Glossary, default_glossary_path
from telsiz.quality.metrics import chrf, corpus_chrf
from telsiz.translate.argos import create_argos_translator
from telsiz.translate.nllb import NLLB_MODELS, create_nllb_translator

ROOT = Path(__file__).resolve().parents[1]


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--phrases", type=Path, default=ROOT / "data/eval/en_tr_phrases.toml")
    parser.add_argument("--source", default="en")
    parser.add_argument("--target", default="tr")
    parser.add_argument("--out", type=Path, help="also write the report to this file")
    parser.add_argument("--no-glossary", action="store_true", help="translate without the glossary")
    parser.add_argument("--engine", choices=["argos", *NLLB_MODELS], default="argos")
    args = parser.parse_args()
    glossary = None if args.no_glossary else Glossary.load(default_glossary_path())

    phrases = tomllib.loads(args.phrases.read_text(encoding="utf-8"))["phrases"]
    if args.engine == "argos":
        translator = create_argos_translator(cpu_threads=4)
    else:
        translator = create_nllb_translator(args.engine, cpu_threads=4)
    translator.prepare([args.source], args.target)
    translator.translate(phrases[0][args.source], args.source, args.target)  # warm-up

    rows = []
    started = time.perf_counter()
    for item in phrases:
        text = item[args.source]
        if glossary is None:
            hypothesis = translator.translate(text, args.source, args.target)
        else:
            protected = glossary.protect(text, args.source, args.target)
            translated = translator.translate(protected.text, args.source, args.target)
            hypothesis = glossary.restore(protected, translated)
        rows.append((item["category"], item[args.source], hypothesis, item[args.target]))
    elapsed_ms = (time.perf_counter() - started) * 1000 / max(len(rows), 1)

    by_category: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for category, _, hypothesis, reference in rows:
        by_category[category].append((hypothesis, reference))

    lines = [
        f"# Translation check: {args.source} -> {args.target} ({args.engine}, "
        f"glossary {'off' if glossary is None else 'on'})",
        "",
        f"{len(rows)} phrases, average {elapsed_ms:.0f} ms per phrase on CPU (4 threads).",
        "chrF compares characters with one reference translation (0-100, higher is closer);",
        "it is a rough guide, read the translations themselves.",
        "",
        "| Category | Phrases | chrF |",
        "|---|---|---|",
    ]
    for category, pairs in by_category.items():
        lines.append(f"| {category} | {len(pairs)} | {corpus_chrf(pairs):.1f} |")
    all_pairs = [p for pairs in by_category.values() for p in pairs]
    lines += [f"| **all** | {len(all_pairs)} | **{corpus_chrf(all_pairs):.1f}** |", ""]
    lines += ["| Category | Source | Telsiz | Reference | chrF |", "|---|---|---|---|---|"]
    for category, source, hypothesis, reference in rows:
        lines.append(
            f"| {category} | {_cell(source)} | {_cell(hypothesis)} | {_cell(reference)} "
            f"| {chrf(hypothesis, reference):.0f} |"
        )

    report = "\n".join(lines) + "\n"
    sys.stdout.reconfigure(encoding="utf-8")
    print(report)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
