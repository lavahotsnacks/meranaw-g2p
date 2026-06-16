import pynini

from meranaw_g2p.config import load_config, resolve_language_directory
from meranaw_g2p.compiler import build_sigma, build_sigma_star, compile_step
from meranaw_g2p.errors import TranscriptionError
from meranaw_g2p.models import LanguageConfig, PipelineContext, PipelineStep
from meranaw_g2p.rules import load_pipeline_steps


def _extract_exceptions(steps: list[PipelineStep]) -> dict[str, str]:
    """Extract exception dictionary from an exceptions.tsv step.

    Exception words bypass the FST cascade entirely. Returns an empty
    dict if no exceptions.tsv step is found or it contains no entries.
    """
    for step in steps:
        if step.filename != "exceptions.tsv":
            continue
        exception_map: dict[str, str] = {}
        for rule in step.rules:
            exception_map[rule.input] = rule.output
        return exception_map
    return {}


def _build_fst_pipeline(
    steps: list[PipelineStep],
    config: LanguageConfig,
    sigma_star: pynini.Fst,
) -> pynini.Fst:
    """Compile all non-exception steps and compose them into one FST.

    Steps are composed in pipeline order: step1 @ step2 @ step3 ...
    The exceptions.tsv step is skipped (handled separately by
    transcribe). Each step is compiled via compile_step, the single
    source of truth for step dispatch.
    """
    compiled: list[pynini.Fst] = []
    for step in steps:
        if step.filename == "exceptions.tsv":
            continue
        compiled.append(compile_step(step, config, sigma_star))

    if not compiled:
        raise RuntimeError(
            "No pipeline steps were compiled. "
            "Ensure the pipeline manifest lists at least one rule file."
        )

    pipeline = compiled[0]
    for fst in compiled[1:]:
        pipeline = (pipeline @ fst).optimize()

    return pipeline


def build_pipeline(lang_code: str) -> PipelineContext:
    """Build the complete G2P pipeline for a language.

    Returns a PipelineContext containing the composed pipeline FST,
    exception dictionary, per-step FSTs for tracing, language config,
    and sigma_star.
    """
    config = load_config(lang_code)
    lang_dir = resolve_language_directory(lang_code)
    steps = load_pipeline_steps(lang_dir, config.pipeline)

    sigma = build_sigma(config)
    sigma_star = build_sigma_star(sigma)

    pipeline_fst = _build_fst_pipeline(steps, config, sigma_star)
    exceptions = _extract_exceptions(steps)

    step_fsts: list[tuple[str, pynini.Fst, PipelineStep]] = []
    for step in steps:
        if step.filename == "exceptions.tsv":
            continue
        step_fsts.append((step.filename, compile_step(step, config, sigma_star), step))

    return PipelineContext(
        fst=pipeline_fst,
        exceptions=exceptions,
        step_fsts=step_fsts,
        config=config,
        sigma_star=sigma_star,
    )


def transcribe(
    word: str,
    ctx: PipelineContext,
) -> list[str]:
    """Transcribe a single word through the G2P pipeline.

    Checks the exception dictionary first, then composes the input with
    the pipeline FST and projects to the output side. Optional rules may
    produce multiple variants (up to 10 unique branches).

    Raises TranscriptionError on FST operation failure.
    """
    word = word.strip()
    if not word:
        return []

    if word in ctx.exceptions:
        return [ctx.exceptions[word]]

    try:
        input_acceptor = pynini.accep(word)
        composed = (input_acceptor @ ctx.fst).optimize()
        output_projection = composed.project("output").optimize()
        shortest = pynini.shortestpath(
            output_projection,
            nshortest=10,
            unique=True,
        )
        transcriptions = list(shortest.paths().ostrings())
        return transcriptions if transcriptions else ["<NO_OUTPUT>"]
    except pynini.FstOpError as e:
        raise TranscriptionError(
            f"FST operation failed for word '{word}': {e}"
        ) from e
