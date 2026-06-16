import csv
import os
from typing import Any

import yaml

from meranaw_g2p.errors import RuleParseError
from meranaw_g2p.models import MappingRule, PipelineStep, RewriteRule


def load_tsv_rules(path: str) -> list[MappingRule]:
    """Read a two-column TSV file (input [tab] output) into MappingRules.

    Skips comment lines starting with '#', empty lines, and header rows
    that match known column names. Returns an empty list if the file
    does not exist.
    """
    if not os.path.exists(path):
        return []

    rules: list[MappingRule] = []
    header_skipped = False
    known_headers = {"input", "output", "grapheme", "phoneme"}

    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if not row:
                continue
            joined = "\t".join(row).strip()
            if not joined or joined.startswith("#"):
                continue
            cells = [c.strip() for c in row if c.strip()]
            if len(cells) < 2:
                continue
            if not header_skipped and cells[0].lower() in known_headers:
                header_skipped = True
                continue
            rules.append(MappingRule(input=cells[0], output=cells[1]))

    return rules


def load_yaml_rules(path: str) -> list[RewriteRule]:
    """Read a YAML rule file into RewriteRule objects.

    Expected structure:
        rules:
          - description: "..."
            input: "..."
            output: "..." | ["...", "..."]
            left: "..." | {class: "...", except: [...]} | null
            right: "..." | {class: "...", except: [...]} | null
            mode: "obligatory" | "optional"
            direction: "ltr" | "rtl" | "simultaneous"
            active: true | false

    Returns an empty list if the file does not exist or contains no rules.
    """
    if not os.path.exists(path):
        return []

    with open(path, encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    if not isinstance(raw, dict) or "rules" not in raw:
        return []

    rules: list[RewriteRule] = []
    for entry in raw["rules"]:
        if not isinstance(entry, dict):
            continue
        active = entry.get("active", True)
        if isinstance(active, str):
            active = active.strip().lower() in ("true", "yes", "1")
        elif not isinstance(active, bool):
            active = True
        rules.append(
            RewriteRule(
                description=entry.get("description", ""),
                input=entry.get("input", ""),
                output=entry.get("output", ""),
                left=entry.get("left"),
                right=entry.get("right"),
                mode=entry.get("mode", "obligatory"),
                direction=entry.get("direction", "ltr"),
                active=active,
            )
        )

    return rules


def load_pipeline_steps(
    lang_dir: str,
    manifest: list[str],
) -> list[PipelineStep]:
    """Load all rule files listed in the pipeline manifest.

    Each filename determines the format:
      .tsv  -> load_tsv_rules()  -> rule_type="mapping"
      .yaml -> load_yaml_rules() -> rule_type="rewrite"
      .yml  -> load_yaml_rules() -> rule_type="rewrite"

    Raises RuleParseError for unknown file extensions.
    """
    steps: list[PipelineStep] = []

    for filename in manifest:
        filepath = os.path.join(lang_dir, filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".tsv":
            rules = load_tsv_rules(filepath)
            steps.append(
                PipelineStep(
                    filename=filename,
                    rule_type="mapping",
                    rules=rules,
                )
            )
        elif ext in (".yaml", ".yml"):
            rules = load_yaml_rules(filepath)
            steps.append(
                PipelineStep(
                    filename=filename,
                    rule_type="rewrite",
                    rules=rules,
                )
            )
        else:
            raise RuleParseError(
                f"Unsupported rule file extension '{ext}' "
                f"in pipeline: {filename}. "
                f"Supported: .tsv, .yaml, .yml."
            )

    return steps
