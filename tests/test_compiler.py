import pytest

from meranaw_g2p.compiler import build_sigma, build_sigma_star, compile_step
from meranaw_g2p.config import load_config, resolve_language_directory
from meranaw_g2p.errors import CompilationError
from meranaw_g2p.models import PipelineStep
from meranaw_g2p.rules import load_tsv_rules


def test_compile_step_mapping():
    config = load_config("meranaw")
    lang_dir = resolve_language_directory("meranaw")
    step = PipelineStep(
        filename="test.tsv",
        rule_type="mapping",
        rules=load_tsv_rules(f"{lang_dir}/case.tsv"),
    )
    sigma = build_sigma(config)
    sigma_star = build_sigma_star(sigma)
    fst = compile_step(step, config, sigma_star)
    assert fst is not None


def test_compile_step_raises_on_unknown_type():
    step = PipelineStep(filename="bad.xyz", rule_type="unknown", rules=[])
    config = load_config("meranaw")
    sigma = build_sigma(config)
    sigma_star = build_sigma_star(sigma)
    with pytest.raises(CompilationError, match="Unknown rule_type"):
        compile_step(step, config, sigma_star)
