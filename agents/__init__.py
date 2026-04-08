
# agents/__init__.py
"""
Agents package for Publication Assistant.

Each agent is responsible for a distinct role in the pipeline.
"""
from .repo_analyzer import RepoAnalyzerAgent
from .metadata_recommender import MetadataRecommenderAgent
from .content_improver import ContentImproverAgent
from .reviewer_critic import ReviewerCriticAgent
from .fact_checker import FactCheckerAgent

__all__ = [
    "RepoAnalyzerAgent",
    "MetadataRecommenderAgent",
    "ContentImproverAgent",
    "ReviewerCriticAgent",
    "FactCheckerAgent",
]
