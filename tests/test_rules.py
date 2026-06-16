from meranaw_g2p.config import load_config, resolve_language_directory
from meranaw_g2p.rules import load_pipeline_steps, load_tsv_rules, load_yaml_rules


_MERANAW_DIR = resolve_language_directory("meranaw")


def test_load_tsv_rules_parses_case_file():
    rules = load_tsv_rules(f"{_MERANAW_DIR}/case.tsv")
    assert len(rules) == 30
    assert rules[0].input == "A"
    assert rules[0].output == "a"


def test_load_tsv_rules_skips_comments_and_header():
    rules = load_tsv_rules(f"{_MERANAW_DIR}/digraphs.tsv")
    assert len(rules) == 3
    assert rules[0].input == "ph"
    assert rules[0].output == "p'"


def test_load_yaml_rules_parses_glottal():
    rules = load_yaml_rules(f"{_MERANAW_DIR}/glottal.yaml")
    assert len(rules) == 4
    assert all(r.active for r in rules)
    assert rules[0].input == "â"
    assert rules[0].output == "aʔ"


def test_load_yaml_rules_returns_empty_for_missing():
    rules = load_yaml_rules(f"{_MERANAW_DIR}/nonexistent.yaml")
    assert rules == []


def test_load_pipeline_steps_returns_correct_count():
    config = load_config("meranaw")
    steps = load_pipeline_steps(_MERANAW_DIR, config.pipeline)
    assert len(steps) >= 4
    step_filenames = [s.filename for s in steps]
    assert "case.tsv" in step_filenames
    assert "digraphs.tsv" in step_filenames
    assert "conventions.tsv" in step_filenames
    assert "glottal.yaml" in step_filenames
