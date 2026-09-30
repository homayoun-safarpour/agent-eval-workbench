from pathlib import Path

from agent_eval_workbench.cli import main

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8-sig")
FAIL_BUNDLE = str(ROOT / "examples" / "forbidden_plus_missing_OUTPUT.json")


def test_readme_spoken_h1_is_workbench():
    assert README.lstrip().startswith("# workbench\n")
    assert "agent-eval-workbench" in README


def test_readme_first_screen_matches_top100_craft():
    pip_at = README.find("pip install")
    interview_at = README.find("Interview pack")
    problem_at = README.find("## The problem")
    assert 0 <= pip_at < interview_at
    assert 0 <= pip_at < problem_at
    head = "\n".join(README.splitlines()[:26])
    assert "# workbench" in head
    assert "git clone https://github.com/homayoun-safarpour/agent-eval-workbench" in head
    assert "pip install -e" in head
    assert "forbidden_plus_missing_OUTPUT.json" in head
    assert "verdict: FAIL" in head
    assert "composite=0.0000" in head
    assert "Interview pack" not in head
    assert "\u2014" not in head
    assert "verdict: PASS" not in head


def test_readme_stranger_score_exits_2():
    code = main(
        [
            "score",
            FAIL_BUNDLE,
            "--min-composite",
            "0.99",
        ]
    )
    assert code == 2
