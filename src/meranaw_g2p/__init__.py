from importlib.metadata import version

from meranaw_g2p.models import PipelineContext, TraceResult
from meranaw_g2p.pipeline import build_pipeline, transcribe
from meranaw_g2p.tracer import trace_transcription

__version__ = version("meranaw-g2p")

__all__ = [
    "PipelineContext",
    "TraceResult",
    "build_pipeline",
    "trace_transcription",
    "transcribe",
]
