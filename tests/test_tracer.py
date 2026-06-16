import pytest

from meranaw_g2p.pipeline import build_pipeline
from meranaw_g2p.tracer import trace_transcription


@pytest.fixture(scope="module")
def pipeline_ctx():
    return build_pipeline("meranaw")


def test_trace_single_branch(pipeline_ctx):
    traces = trace_transcription("philian", pipeline_ctx)
    assert len(traces) == 1
    t = traces[0]
    assert t.transcription == "p'iliyan"
    assert "digraphs.tsv" in t.trace_files
    assert "hiatus.yaml" in t.trace_files
    assert "ph→p'" in t.trace_rules
    assert "Glide y epenthesis" in t.trace_rules
    assert "philian" in t.trace_steps
    assert "p'ilian" in t.trace_steps
    assert "p'iliyan" in t.trace_steps


def test_trace_empty_word(pipeline_ctx):
    traces = trace_transcription("", pipeline_ctx)
    assert len(traces) == 1
    assert traces[0].transcription == ""


def test_trace_cascade_ordering(pipeline_ctx):
    traces = trace_transcription("thaloan", pipeline_ctx)
    t = traces[0]
    steps_parts = t.trace_steps.split(" > ")
    assert steps_parts[0] == "thaloan"
    assert steps_parts[-1] == "t'alowan"
    assert "digraphs.tsv" in t.trace_files
    assert "hiatus.yaml" in t.trace_files
    rules_order = t.trace_files
    assert rules_order.index("digraphs.tsv") < rules_order.index("hiatus.yaml")
