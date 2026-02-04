# agents/fact_checker.py
from dataclasses import dataclass
from typing import List
from tools.arxiv_scholar import ArxivScholarTool
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class FactCheckResult:
    claims_found: List[str]
    verified: List[str]
    flagged: List[str]


class FactCheckerAgent:
    """
    Fact-checker that extracts claims and looks up papers on arXiv to verify them.
    """

    def __init__(self, scholar_tool: ArxivScholarTool):
        self.scholar = scholar_tool

    def run(self, readme_text: str) -> FactCheckResult:
        logger.info("FactCheckerAgent: extracting claims")

        # Simple extraction of "scientific" looking sentences
        # In production this would use an LLM extractor
        sentences = re.split(r'[.!?]', readme_text)
        claims = [s.strip() for s in sentences if len(s) > 30 and
                  any(w in s.lower() for w in ["novel", "state-of-the-art", "outperforms", "significant", "paper", "proposed"])]

        verified = []
        flagged = []

        for c in claims[:3]:  # Limit checks to avoid rate limits
            logger.info(f"Verifying claim: {c[:50]}...")
            hits = self.scholar.search(c, max_results=1)
            if hits:
                verified.append(f"{c} (Found paper: {hits[0]['title']})")
            else:
                flagged.append(f"{c} (No direct match found)")

        result = FactCheckResult(
            claims_found=claims, verified=verified, flagged=flagged)
        return result
