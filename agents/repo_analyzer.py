# agents/repo_analyzer.py
from dataclasses import dataclass
from typing import Dict, Any, List
from tools.repo_parser import RepoParser

import logging
logger = logging.getLogger(__name__)


@dataclass
class RepoAnalysis:
    files: Dict[str, str]
    readme: str
    summary: str
    code_stats: Dict[str, Any]
    missing_sections: List[str]


class RepoAnalyzerAgent:
    """
    Agent that analyzes a repository structure (README, code, notebooks).
    Responsibilities:
      - Parse repo files
      - Extract README content, list files
      - Produce basic code metrics (line counts, languages)
      - Detect missing documentation sections
    """

    def __init__(self, repo_source: str, repo_parser: RepoParser):
        self.repo_source = repo_source
        self.parser = repo_parser

    def run(self) -> RepoAnalysis:
        logger.info("RepoAnalyzerAgent: parsing repository %s",
                    self.repo_source)
        parsed = self.parser.parse(self.repo_source)
        readme = parsed.get("README.md") or parsed.get("README") or ""
        code_stats = self._compute_code_stats(parsed.get("files", {}))
        missing = self._detect_missing_sections(readme)
        # derive a short summary from the README (first non-empty paragraph)
        summary = ""
        for part in (p.strip() for p in readme.split("\n\n") if p.strip()):
            summary = part
            break
        if not summary:
            summary = parsed.get("title", "")

        analysis = RepoAnalysis(
            files=parsed.get("files", {}), readme=readme, summary=summary, code_stats=code_stats, missing_sections=missing
        )
        # Return analysis directly (message bus removed)
        logger.debug("RepoAnalyzerAgent: analysis completed")
        return analysis

    def _compute_code_stats(self, files: Dict[str, str]) -> Dict[str, Any]:
        languages = {}
        total_lines = 0
        for fname, content in files.items():
            total_lines += content.count("\n") + 1
            ext = fname.split(".")[-1] if "." in fname else "txt"
            languages[ext] = languages.get(ext, 0) + 1
        return {"file_count": len(files), "languages": languages, "total_lines": total_lines}

    def _detect_missing_sections(self, readme: str) -> List[str]:
        required = ["Installation", "Usage", "License",
                    "Contributing", "Credits", "Examples"]
        missing = [r for r in required if r.lower() not in readme.lower()]
        return missing
