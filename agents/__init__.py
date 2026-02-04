# # agents/__init__.py
# # Initializes the agents module
# # This file can be empty or export agents
# from .repo_analyzer import RepoAnalyzer
# from .metadata_recommender import MetadataRecommender
# from .content_improver import ContentImprover
# from .reviewer_critic import ReviewerCritic
# from .fact_checker import FactChecker


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
