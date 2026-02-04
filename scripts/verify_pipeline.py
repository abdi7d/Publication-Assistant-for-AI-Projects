import sys
import os
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestration.graph import Orchestrator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_pipeline():
    logger.info("Starting pipeline verification...")

    # Mock agents to avoid external dependency calls (API keys, network) during verification
    mock_repo_agent = MagicMock()
    mock_repo_agent.run.return_value = MagicMock(
        readme="# Sample Project", 
        files={"README.md": "# Sample Project"},
        code_stats={"file_count": 1, "languages": {"md": 1}}
    )

    mock_meta_agent = MagicMock()
    mock_meta_agent.run.return_value = MagicMock(
        title_suggestions=["Sample Title"],
        tags=["sample", "project"],
        short_description="A sample project."
    )

    mock_content_agent = MagicMock()
    mock_content_agent.run.return_value = MagicMock(
        improved_readme="# Improved Sample Project"
    )

    mock_review_agent = MagicMock()
    mock_review_agent.run.return_value = MagicMock(
        score=10,
        issues=[],
        recommendations=[]
    )

    mock_fact_agent = MagicMock()
    mock_fact_agent.run.return_value = MagicMock(
        verified=[],
        flagged=[]
    )

    agents = {
        "repo_analyzer": mock_repo_agent,
        "metadata_recommender": mock_meta_agent,
        "content_improver": mock_content_agent,
        "reviewer_critic": mock_review_agent,
        "fact_checker": mock_fact_agent,
    }

    try:
        orch = Orchestrator()
        logger.info("Orchestrator initialized.")
        
        results = orch.run_pipeline(agents, "http://dummy-repo-url")
        logger.info("Pipeline execution completed.")
        
        # Verify specific keys in output
        expected_keys = ["analysis", "metadata", "content_improvement", "review", "fact_check"]
        missing_keys = [k for k in expected_keys if k not in results]
        
        if missing_keys:
            logger.error(f"Missing keys in result: {missing_keys}")
            sys.exit(1)
            
        logger.info("Verification SUCCESS: All expected keys present in pipeline output.")

    except Exception as e:
        logger.exception(f"Verification FAILED with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_pipeline()
