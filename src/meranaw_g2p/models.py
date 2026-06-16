# Typed data containers for rule definitions, configuration, and pipeline metadata.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    import pynini

RuleOutput = Union[str, list[str]]
"""Union type for rewrite rule outputs: a single string or multiple variants."""


@dataclass
class MappingRule:
    """A single context-free grapheme-to-phoneme mapping (one TSV row)."""

    input: str
    output: str


@dataclass
class RewriteRule:
    """A context-sensitive rewrite rule with optional environments.

    Uses standard phonological notation: input -> output / left _ right.
    Left and right contexts accept plain strings, character classes from
    LanguageConfig.sets, or None (empty context).

    When output is a list, the compiler produces a branching transducer
    where each variant is an equally valid path.
    """

    description: str = ""
    input: str = ""
    output: RuleOutput = ""
    left: Optional[str | list[str] | dict[str, object]] = None
    right: Optional[str | list[str] | dict[str, object]] = None
    mode: str = "obligatory"
    direction: str = "ltr"
    active: bool = True


@dataclass
class LanguageAlphabet:
    """Character inventory for a language: graphemes, phonemes, special symbols."""

    graphemes: list[str] = field(default_factory=list)
    phonemes: list[str] = field(default_factory=list)
    special_symbols: list[str] = field(default_factory=list)


@dataclass
class LanguageConfig:
    """Top-level configuration read from language.yaml."""

    language: str = ""
    iso: str = ""
    alphabet: LanguageAlphabet = field(default_factory=LanguageAlphabet)
    sets: dict[str, list[str]] = field(default_factory=dict)
    pipeline: list[str] = field(default_factory=list)


@dataclass
class PipelineStep:
    """One rule file parsed into typed rules (TSV or YAML)."""

    filename: str = ""
    rule_type: str = ""
    rules: list[MappingRule | RewriteRule] = field(default_factory=list)


@dataclass
class TraceResult:
    """Trace output from a single-word transcription through the pipeline."""

    transcription: str = ""
    trace_files: str = ""
    trace_rules: str = ""
    trace_steps: str = ""


@dataclass
class PipelineContext:
    """All data needed to transcribe and trace through a G2P pipeline.

    Built by build_pipeline() and passed to transcribe() and
    trace_transcription(). Callers access fields by name instead of
    destructuring an ambiguous tuple.
    """

    fst: "pynini.Fst"
    exceptions: dict[str, str]
    step_fsts: list[tuple[str, "pynini.Fst", PipelineStep]]
    config: LanguageConfig
    sigma_star: "pynini.Fst"
