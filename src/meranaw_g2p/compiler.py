# Compiles parsed rule models into Pynini finite-state transducers.

import pynini
from typing import Any, Optional

from meranaw_g2p.errors import CompilationError
from meranaw_g2p.models import LanguageConfig, MappingRule, PipelineStep, RewriteRule


# -- Sigma (universal alphabet) -----------------------------------------------

def build_sigma(config: LanguageConfig) -> pynini.Fst:
    """Build the sigma acceptor containing every character in the language.

    Required by cdrewrite as the universal alphabet. Includes graphemes,
    phonemes, and special symbols (boundary markers).
    """
    all_characters: set[str] = set()
    all_characters.update(config.alphabet.graphemes)
    all_characters.update(config.alphabet.phonemes)
    all_characters.update(config.alphabet.special_symbols)

    char_fsts = [pynini.accep(char) for char in sorted(all_characters)]

    if not char_fsts:
        raise ValueError(
            "Cannot build sigma: no characters defined in language configuration."
        )

    return pynini.union(*char_fsts).optimize()


def build_sigma_star(sigma: pynini.Fst) -> pynini.Fst:
    """Build sigma* (Kleene closure), the mandatory fourth argument to cdrewrite."""
    return pynini.closure(sigma).optimize()


# -- Context resolution -------------------------------------------------------

def _resolve_character_list(
    specification: Any,
    config: LanguageConfig,
) -> Optional[pynini.Fst]:
    """Convert a rule context specification into a Pynini acceptor.

    Accepts:
      - A plain string: matched literally.
      - A list of strings: union of all characters.
      - A dict with 'class' key: references a named set from config.sets.
        The special class "*" expands to every character in the alphabet
        plus the end-of-string boundary marker.
      - A dict with 'class' and 'except' keys: the named set minus the
        excluded characters.
      - None: empty context.
    """
    if specification is None:
        return None

    if isinstance(specification, str):
        return pynini.accep(specification).optimize()

    if isinstance(specification, list):
        acceptors = [pynini.accep(c).optimize() for c in specification]
        if not acceptors:
            return None
        return pynini.union(*acceptors).optimize()

    if isinstance(specification, dict):
        class_name = specification.get("class")
        if class_name is None:
            return None

        if class_name == "*":
            all_characters: set[str] = set()
            all_characters.update(config.alphabet.graphemes)
            all_characters.update(config.alphabet.phonemes)
            all_characters.update(config.alphabet.special_symbols)

            char_acceptors = [
                pynini.accep(c).optimize() for c in sorted(all_characters)
            ]
            if not char_acceptors:
                return None
            base_acceptor = pynini.union(*char_acceptors).optimize()
        else:
            class_members = config.sets.get(class_name, [])
            if not class_members:
                raise ValueError(
                    f"Referenced character class '{class_name}' is "
                    f"not defined in language configuration sets."
                )

            base_acceptor = pynini.union(
                *[pynini.accep(c).optimize() for c in class_members]
            ).optimize()

        excluded = specification.get("except", [])
        if excluded:
            if isinstance(excluded, str):
                excluded = [excluded]
            exclusion_acceptor = pynini.union(
                *[pynini.accep(c).optimize() for c in excluded]
            ).optimize()
            base_acceptor = pynini.difference(
                base_acceptor, exclusion_acceptor
            ).optimize()

        if class_name == "*":
            base_acceptor = pynini.union(
                base_acceptor,
                pynini.accep("[EOS]").optimize(),
            ).optimize()

        return base_acceptor

    raise TypeError(
        f"Unsupported context specification type: {type(specification)}. "
        f"Expected str, list, dict, or None."
    )


# -- Mapping rules (TSV) ------------------------------------------------------

def compile_mapping_rules(
    rules: list[MappingRule],
    sigma_star: pynini.Fst,
) -> pynini.Fst:
    """Compile context-free mapping rules into a single cdrewrite FST.

    Each rule becomes a pynini.cross operation. All crosses are unioned
    and wrapped in a context-free cdrewrite. Returns sigma_star (identity)
    if the rule list is empty.
    """
    if not rules:
        return sigma_star

    mapping_transducers = [
        pynini.cross(rule.input, rule.output) for rule in rules
    ]

    combined_mapping = pynini.union(*mapping_transducers).optimize()
    return pynini.cdrewrite(combined_mapping, "", "", sigma_star).optimize()


def compile_single_mapping(
    rule: MappingRule,
    sigma_star: pynini.Fst,
) -> pynini.Fst:
    """Compile a single mapping rule into its own cdrewrite for per-rule tracing."""
    mapping = pynini.cross(rule.input, rule.output)
    return pynini.cdrewrite(mapping, "", "", sigma_star).optimize()


# -- Rewrite rules (YAML) -----------------------------------------------------

def compile_rewrite_rule(
    rule: RewriteRule,
    config: LanguageConfig,
    sigma_star: pynini.Fst,
) -> Optional[pynini.Fst]:
    """Compile one RewriteRule into a context-dependent cdrewrite FST.

    When output is a list, each variant becomes a separate cross product
    and all are unioned to create a branching transducer.
    """
    if not rule.active:
        return None

    if isinstance(rule.output, list):
        if not rule.output:
            return None
        mapping = pynini.union(
            *[pynini.cross(rule.input, out) for out in rule.output]
        ).optimize()
    else:
        mapping = pynini.cross(rule.input, rule.output)

    left_acceptor = _resolve_character_list(rule.left, config)
    right_acceptor = _resolve_character_list(rule.right, config)

    left_context = left_acceptor if left_acceptor is not None else ""
    right_context = right_acceptor if right_acceptor is not None else ""

    mode = "opt" if rule.mode == "optional" else "obl"

    return pynini.cdrewrite(
        mapping,
        left_context,
        right_context,
        sigma_star,
        direction=rule.direction,
        mode=mode,
    ).optimize()


def compile_rewrite_rules(
    rules: list[RewriteRule],
    config: LanguageConfig,
    sigma_star: pynini.Fst,
) -> pynini.Fst:
    """Compile a list of RewriteRules into a single composed FST.

    Active rules are compiled individually and composed in order with @.
    Returns sigma_star (identity) if no active rules.
    """
    compiled: list[pynini.Fst] = []

    for rule in rules:
        fst = compile_rewrite_rule(rule, config, sigma_star)
        if fst is not None:
            compiled.append(fst)

    if not compiled:
        return sigma_star

    result = compiled[0]
    for fst in compiled[1:]:
        result = (result @ fst).optimize()

    return result


# -- Step dispatcher (single source of truth) ----------------------------------

def compile_step(
    step: PipelineStep,
    config: LanguageConfig,
    sigma_star: pynini.Fst,
) -> pynini.Fst:
    """Dispatch a PipelineStep to the correct compiler.

    Single source of truth for "given a step object, produce its FST."
    Used by pipeline.py (for composition) and tracer.py (for per-step FSTs).

    Raises CompilationError on unknown rule_type.
    """
    if step.rule_type == "mapping":
        return compile_mapping_rules(step.rules, sigma_star)
    if step.rule_type == "rewrite":
        return compile_rewrite_rules(step.rules, config, sigma_star)
    raise CompilationError(f"Unknown rule_type: {step.rule_type}")
