# meranaw-g2p

Grapheme-to-Phoneme (G2P) conversion for the Meranaw language using finite-state transducers.

Built on Pynini, a Python library for finite-state grammar compilation.

## Features

- Phonological rule compilation via Pynini FSTs
- Context-sensitive rewrite rules
- Exception dictionary for irregular words
- Branch-aware tracing for rule-level debugging
- Packaged language data for Meranaw

## Installation

```bash
pip install meranaw-g2p
```

## Quick Start

```python
from meranaw_g2p import build_pipeline, transcribe

pipeline = build_pipeline("meranaw")

transcribe("dî", pipeline)        # ["diʔ"]
transcribe("philian", pipeline)    # ["p'iliyan"]
transcribe("endô", pipeline)       # ["əndoʔ"]
```

## License

MIT
