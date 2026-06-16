import pytest

from meranaw_g2p.pipeline import build_pipeline, transcribe


@pytest.fixture(scope="module")
def pipeline_ctx():
    return build_pipeline("meranaw")


def test_build_pipeline_returns_valid_context(pipeline_ctx):
    assert pipeline_ctx.fst is not None
    assert isinstance(pipeline_ctx.exceptions, dict)
    assert len(pipeline_ctx.step_fsts) > 0


def test_transcribe_empty(pipeline_ctx):
    assert transcribe("", pipeline_ctx) == []
    assert transcribe("   ", pipeline_ctx) == []


def test_transcribe_simple_digraph(pipeline_ctx):
    assert transcribe("philian", pipeline_ctx) == ["p'iliyan"]


def test_transcribe_multi_digraph(pipeline_ctx):
    assert transcribe("phakainengkaan", pipeline_ctx) == ["p'akainəŋkaan"]


def test_transcribe_glottal_resolution(pipeline_ctx):
    assert transcribe("endô", pipeline_ctx) == ["əndoʔ"]
    assert transcribe("dî", pipeline_ctx) == ["diʔ"]
    assert transcribe("watâ", pipeline_ctx) == ["wataʔ"]
    assert transcribe("batî", pipeline_ctx) == ["batiʔ"]
    assert transcribe("kakâ", pipeline_ctx) == ["kakaʔ"]


def test_transcribe_cascade_order(pipeline_ctx):
    assert transcribe("thaloan", pipeline_ctx) == ["t'alowan"]
    assert transcribe("phamoadan", pipeline_ctx) == ["p'amowadan"]


def test_transcribe_non_meranaw_word(pipeline_ctx):
    assert transcribe("xyz123", pipeline_ctx) == ["<NO_OUTPUT>"]
