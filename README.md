# meranaw-g2p

<p align="center">
───────────────────────────────────────────────<br>
 ⊹ ࣪ ˖ ૮( ˶ᵔ ᵕ ᵔ˶ )っ  meranaw-g2p vers. 0.1.0<br>
───────────────────────────────────────────────
</p>

Grapheme-to-Phoneme (G2P) conversion for the Meranaw language using finite-state transducers.

Built on [Pynini](http://pynini.opengrm.org/), a Python library for finite-state grammar compilation.

## Installation

```bash
pip install meranaw-g2p
```

## Usage

```python
from meranaw_g2p import build_pipeline, transcribe

pipeline = build_pipeline("meranaw")

results = transcribe("miapasad", pipeline)
print(results)  # ["miyapasad"]  Notes: 'achievement' — hiatus glide epenthesis

results = transcribe("phangangaleken", pipeline)
print(results)  # ["p'aŋaŋaləkən"]  Notes: 'frighten' — full cascade: digraph + nasal + schwa

# Minimal pair: th (ejective) vs t (plain) changes meaning
results = transcribe("bethang", pipeline)
print(results)  # ["bət'aŋ"]  Notes: 'crazy' — ejective t' from th digraph
results = transcribe("betang", pipeline)
print(results)  # ["bətaŋ"]  Notes: 'dowry' — plain t, no ejective

results = transcribe("tiphô", pipeline)
print(results)  # ["tip'oʔ"]  Notes: 'jump down' — digraph + word-final glottal stop
```

## Development

```bash
git clone https://github.com/lavahotsnacks/meranaw-g2p
cd meranaw-g2p
pip install -e .
pytest
```

## License

MIT

```
                                  |
                                 |||
                                |||||
                  |    |    |   |||||||
                 )_)  )_)  )_)   ~|~
                )___))___))___)\  |
               )____)____)_____)\\|
             _____|____|____|_____\\\__
             \                       /
       ~^~^~~^~^~~^~^~~^~^~~^~^~~^~^~~^~^~~^~^~
               ~^~  all aboard!  ~^~
       ~^~^~~^~^~~^~^~~^~^~~^~^~~^~^~~^~^~~^~^~
```
