import pynini

from meranaw_g2p.compiler import compile_single_mapping, compile_rewrite_rule
from meranaw_g2p.errors import TraceError
from meranaw_g2p.models import LanguageConfig, PipelineContext, PipelineStep, TraceResult


def _trace_step_rules(
    word: str,
    step: PipelineStep,
    config: LanguageConfig,
    sigma_star: pynini.Fst,
) -> list[str]:
    """Identify which individual rules in a step triggered on the current word.

    Each TSV rule is compiled into a standalone cdrewrite. Each active
    YAML rule is compiled individually. A rule is triggered if running
    it produces output that differs from the input.
    """
    triggered: list[str] = []

    if step.rule_type == "mapping":
        for rule in step.rules:
            try:
                rule_fst = compile_single_mapping(rule, sigma_star)
                input_acceptor = pynini.accep(word)
                composed = (input_acceptor @ rule_fst).optimize()
                output_projection = composed.project("output").optimize()
                shortest = pynini.shortestpath(
                    output_projection, nshortest=1, unique=True
                )
                result = list(shortest.paths().ostrings())[0]
                if result != word:
                    triggered.append(f"{rule.input}→{rule.output}")
            except pynini.FstOpError:
                continue

    elif step.rule_type == "rewrite":
        for rule in step.rules:
            if not rule.active:
                continue
            try:
                rule_fst = compile_rewrite_rule(rule, config, sigma_star)
                if rule_fst is None:
                    continue
                input_acceptor = pynini.accep(word)
                composed = (input_acceptor @ rule_fst).optimize()
                output_projection = composed.project("output").optimize()
                shortest = pynini.shortestpath(
                    output_projection, nshortest=1, unique=True
                )
                result = list(shortest.paths().ostrings())[0]
                if result != word:
                    triggered.append(rule.description)
            except pynini.FstOpError:
                continue

    return triggered


def _match_intermediate_to_target(
    candidates: list[str],
    target: str,
    step_fsts: list[tuple[str, pynini.Fst, PipelineStep]],
    start_index: int,
) -> str:
    """Select the intermediate form whose downstream output matches target.

    Runs each candidate through the remaining step FSTs and returns the
    one whose final output equals target_output.

    Raises TraceError if no candidate matches the target branch.
    """
    if start_index >= len(step_fsts):
        for candidate in candidates:
            if candidate == target:
                return candidate
        raise TraceError(
            f"No candidate intermediate form matches target '{target}' "
            f"at final step."
        )

    for candidate in candidates:
        intermediate = candidate
        for _, fst, _ in step_fsts[start_index:]:
            try:
                acc = pynini.accep(intermediate)
                comp = (acc @ fst).optimize()
                proj = comp.project("output").optimize()
                sp = pynini.shortestpath(proj, nshortest=1, unique=True)
                intermediate = list(sp.paths().ostrings())[0]
            except pynini.FstOpError:
                break
        if intermediate == target:
            return candidate

    raise TraceError(
        f"No intermediate form among {candidates} produces target "
        f"'{target}' when run through remaining steps."
    )


def _trace_one_branch(
    word: str,
    target_output: str,
    step_fsts: list[tuple[str, pynini.Fst, PipelineStep]],
    config: LanguageConfig,
    sigma_star: pynini.Fst,
) -> TraceResult:
    """Trace the transformation path from word to a specific target branch.

    At each step, if multiple intermediate forms are possible, all are
    enumerated and the one whose downstream path matches target_output is
    selected. This ensures per-branch rule traces correspond to the
    actual decision path that produced the branch.
    """
    trace_files_parts: list[str] = []
    trace_rules_parts: list[str] = []
    trace_steps_parts: list[str] = [word]
    current = word

    for i, (filename, step_fst, step_metadata) in enumerate(step_fsts):
        try:
            input_acceptor = pynini.accep(current)
            composed = (input_acceptor @ step_fst).optimize()
            output_projection = composed.project("output").optimize()
            shortest = pynini.shortestpath(
                output_projection, nshortest=10, unique=True
            )
            step_outputs = list(shortest.paths().ostrings())
        except pynini.FstOpError:
            step_outputs = []

        if not step_outputs:
            selected = current
        elif len(step_outputs) == 1:
            selected = step_outputs[0]
        else:
            selected = _match_intermediate_to_target(
                step_outputs, target_output, step_fsts, i + 1
            )

        if selected != current:
            trace_files_parts.append(filename)
            trace_steps_parts.append(selected)
            triggered = _trace_step_rules(
                current, step_metadata, config, sigma_star
            )
            if triggered:
                trace_rules_parts.append(
                    f"{filename}:{','.join(triggered)}"
                )
            else:
                trace_rules_parts.append(filename)

        current = selected

    return TraceResult(
        transcription=current,
        trace_files=", ".join(trace_files_parts) if trace_files_parts else "",
        trace_rules="; ".join(trace_rules_parts) if trace_rules_parts else "",
        trace_steps=" > ".join(trace_steps_parts),
    )


def trace_transcription(
    word: str,
    ctx: PipelineContext,
) -> list[TraceResult]:
    """Transcribe a word while recording which rules fired and intermediate forms.

    Discovers all output branches via the composed pipeline FST, then
    traces each branch through the per-step FSTs to identify which rules
    fired and what intermediate forms were produced.

    When the word is in the exception dictionary, returns a single
    TraceResult with the exception lookup path. When only one branch
    exists, returns a single-element list (no separate single-branch
    function needed).

    Raises TraceError if a branch cannot be matched through the step FSTs.
    """
    word = word.strip()
    if not word:
        return [TraceResult()]

    if word in ctx.exceptions:
        transcription = ctx.exceptions[word]
        return [
            TraceResult(
                transcription=transcription,
                trace_files="exceptions.tsv",
                trace_rules="exceptions: direct lookup",
                trace_steps=f"{word} > {transcription}",
            )
        ]

    try:
        input_acceptor = pynini.accep(word)
        composed = (input_acceptor @ ctx.fst).optimize()
        output_projection = composed.project("output").optimize()
        shortest = pynini.shortestpath(
            output_projection, nshortest=10, unique=True
        )
        all_outputs = list(shortest.paths().ostrings())
    except pynini.FstOpError as e:
        raise TraceError(
            f"FST operation failed during trace for word '{word}': {e}"
        ) from e

    if not all_outputs:
        return [TraceResult(transcription="<NO_OUTPUT>")]

    results: list[TraceResult] = []
    for target_output in all_outputs:
        result = _trace_one_branch(
            word, target_output, ctx.step_fsts, ctx.config, ctx.sigma_star
        )
        results.append(result)

    return results
