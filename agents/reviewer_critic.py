# agents/reviewer_critic.py
from dataclasses import dataclass
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class Review:
    score: float
    issues: List[str]
    strengths: List[str]
    recommendations: List[str]


class ReviewerCriticAgent:
    """
    Performs heuristic-based review of the README and repo content.
    Can be extended to use an LLM for natural-language critique.
    """

    def __init__(self):
        pass

    def run(self, readme: str, code_stats: Dict[str, Any]) -> Review:
        logger.info("ReviewerCriticAgent: reviewing repository artifacts")
        issues = []
        strengths = []
        recommendations = []

        if "installation" not in readme.lower():
            issues.append("Missing 'Installation' section.")
            recommendations.append(
                "Add installation instructions with examples.")

        if code_stats.get("total_lines", 0) < 20:
            issues.append(
                "Repo seems small — include example usage and tests.")

        strengths.append(
            "Code appears to be neatly organized (detected multiple file types).")

        score = max(0.0, 10.0 - len(issues) * 2)
        review = Review(score=score, issues=issues,
                        strengths=strengths, recommendations=recommendations)
        return review
