# main.py
"""
Entry point for the Publication Assistant multi-agent system.

Example usage:
    python main.py --repo-path ./some_repo
"""
from tools import RepoParser, KeywordExtractor, WebSearchTool, RAGRetriever, ArxivScholarTool
import argparse
from agents import RepoAnalyzerAgent, MetadataRecommenderAgent, ContentImproverAgent, ReviewerCriticAgent, FactCheckerAgent
from orchestration import Orchestrator
import os
import logging
from dotenv import load_dotenv
from utils.logging import configure_logging

load_dotenv()
configure_logging()
logger = logging.getLogger(__name__)


def build_agents(repo_source: str):
    repo_parser = RepoParser()
    repo_analyzer = RepoAnalyzerAgent(
        repo_source=repo_source, repo_parser=repo_parser)
    keyword_extractor = KeywordExtractor()
    metadata_recommender = MetadataRecommenderAgent(
        keyword_extractor=keyword_extractor)
    web_search = WebSearchTool()
    rag_retriever = RAGRetriever()
    content_improver = ContentImproverAgent(
        web_search=web_search, rag=rag_retriever)
    reviewer = ReviewerCriticAgent()
    scholar = ArxivScholarTool()
    fact_checker = FactCheckerAgent(scholar_tool=scholar)
    agents = {
        "repo_analyzer": repo_analyzer,
        "metadata_recommender": metadata_recommender,
        "content_improver": content_improver,
        "reviewer_critic": reviewer,
        "fact_checker": fact_checker
    }
    return agents


def main():
    parser = argparse.ArgumentParser("Publication Assistant")
    parser.add_argument("--repo-path", required=True,
                        help="Path to repository directory or zip file")
    args = parser.parse_args()
    repo_path = args.repo_path
    agents = build_agents(repo_path)
    orchestrator = Orchestrator()
    result = orchestrator.run_pipeline(agents=agents, repo_source=repo_path)
    # Print a concise report
    print("=== Publication Assistant Report ===")
    print("Suggested titles:", result["metadata"].title_suggestions)
    print("Suggested tags:", ", ".join(result["metadata"].tags[:20]))
    print("Review score:", result["review"].score)
    print("Missing README sections:", result["analysis"].missing_sections)
    print("Fact-check flagged items:", len(result["fact_check"].flagged))


if __name__ == "__main__":
    main()
