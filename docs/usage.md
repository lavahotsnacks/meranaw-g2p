# Usage

## Basic Transcription

```python
from meranaw_g2p import build_pipeline, transcribe

pipeline = build_pipeline("meranaw")

results = transcribe("philian", pipeline)
print(results)  # ["p'iliyan"]
```

The `build_pipeline()` function compiles all phonological rules into a finite-state transducer cascade. This is a one-time cost — reuse the returned `PipelineContext` for all subsequent transcriptions.

## Tracing

For rule-level debugging, use `trace_transcription()`:

```python
from meranaw_g2p import trace_transcription

traces = trace_transcription("thaloan", pipeline)
t = traces[0]
print(t.transcription)   # "t'alowan"
print(t.trace_files)     # "digraphs.tsv, hiatus.yaml"
print(t.trace_rules)     # "digraphs.tsv:th→t'; hiatus.yaml:Glide w epenthesis"
print(t.trace_steps)     # "thaloan > t'aloan > t'alowan"
```

## Multiple Output Branches

Some words produce multiple valid pronunciations due to optional rules:

```python
traces = trace_transcription("karat", pipeline)
for t in traces:
    print(t.transcription, t.trace_rules)
```

Each branch gets its own `TraceResult` with a complete rule trace.
