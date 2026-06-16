class PipelineError(Exception):
    """Base exception for all engine errors."""


class ConfigError(PipelineError):
    """Invalid or missing language configuration."""


class RuleParseError(PipelineError):
    """Malformed TSV or YAML rule file."""


class CompilationError(PipelineError):
    """Pynini compilation failure or unknown rule type."""


class TranscriptionError(PipelineError):
    """FST operation failed during transcription."""


class TraceError(PipelineError):
    """Tracing cannot resolve a pronunciation branch."""
