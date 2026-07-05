# orchestration/graph.py
from langgraph.graph import StateGraph, END  # type: ignore
import logging
from typing import Any, Dict

from utils.evaluation import evaluate_recommendations

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, bus: Any = None):
        logger.info("Initializing Orchestrator with LangGraph")
        self.bus = bus

    def run_pipeline(self, agents: Dict[str, Any], repo_source: str, style: str = "Technical Blog", goal: str = ""):
        """Run pipeline using LangGraph."""
        logger.info(
            f"Orchestrator: executing pipeline (Style: {style}, Goal: {goal})")

        workflow = StateGraph(dict)

        def analyze_repo(state):
            repo_analysis = agents["repo_analyzer"].run()
            return {**state, "repo_analysis": repo_analysis}

        def recommend_metadata(state):
            repo_analysis = state.get("repo_analysis")
            if not repo_analysis:
                raise ValueError("Repo analysis missing in state")
            metadata = agents["metadata_recommender"].run(
                repo_analysis.readme, repo_analysis.files)
            return {**state, "metadata": metadata}

        def improve_content(state):
            repo_analysis = state.get("repo_analysis")
            if repo_analysis is None:
                logger.error("repo_analysis missing in improve_content")
            metadata = state.get("metadata")
            # style and goal are already in state from inputs
            style_val = state.get("style", "Technical Blog")
            goal_val = state.get("goal", "")
            content_improvement = agents["content_improver"].run(
                repo_analysis.readme, metadata, style=style_val, goal=goal_val)
            return {**state, "content_improvement": content_improvement}

        def review_content(state):
            content = state.get("content_improvement")
            repo_analysis = state.get("repo_analysis")
            review = agents["reviewer_critic"].run(
                getattr(content, 'improved_readme', ''), getattr(repo_analysis, 'code_stats', {}))
            return {**state, "review": review}

        def fact_check(state):
            repo_analysis = state.get("repo_analysis")
            fact_issues = agents["fact_checker"].run(
                getattr(repo_analysis, 'readme', ''))
            return {**state, "fact_check": fact_issues}

        workflow.add_node("analyze_repo", analyze_repo)
        workflow.add_node("recommend_metadata", recommend_metadata)
        workflow.add_node("improve_content", improve_content)
        workflow.add_node("review_content", review_content)
        workflow.add_node("fact_check", fact_check)

        workflow.set_entry_point("analyze_repo")
        workflow.add_edge("analyze_repo", "recommend_metadata")
        workflow.add_edge("recommend_metadata", "improve_content")
        workflow.add_edge("improve_content", "review_content")
        workflow.add_edge("review_content", "fact_check")
        workflow.add_edge("fact_check", END)

        compiled = workflow.compile()
        inputs = {
            "repo_source": repo_source,
            "style": style,
            "goal": goal
        }
        result = compiled.invoke(inputs)

        metadata = result.get("metadata")
        evaluation = evaluate_recommendations(metadata) if metadata is not None else {
            "tag_count": 0,
            "title_count": 0,
            "has_description": 0.0,
            "mock_score": 0.0,
        }

        return {
            "analysis": result.get("repo_analysis"),
            "metadata": metadata,
            "content_improvement": result.get("content_improvement"),
            "review": result.get("review"),
            "fact_check": result.get("fact_check"),
            "evaluation": evaluation,
        }
