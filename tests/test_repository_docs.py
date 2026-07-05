from pathlib import Path


def test_readme_contains_essential_sections():
    repo_root = Path(__file__).resolve().parents[1]
    readme = (repo_root / "README.md").read_text(encoding="utf-8")

    assert "## Overview" in readme
    assert "## Installation" in readme
    assert "## Usage" in readme
    assert "## License" in readme
