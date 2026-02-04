# agents/content_improver.py
from dataclasses import dataclass
from typing import Dict, Any
from tools.web_search import WebSearchTool
from tools.rag_retriever import RAGRetriever
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContentImprovement:
    improved_readme: str
    suggested_images: Dict[str, str]


class ContentImproverAgent:
    """
    Uses an LLM provider (via web_search) to propose improved README content and suggest visuals.
    """

    def __init__(self, web_search: WebSearchTool, rag: RAGRetriever):
        self.web_search = web_search
        self.rag = rag

    def run(self, readme: str, metadata: Dict[str, Any]) -> ContentImprovement:
        logger.info("ContentImproverAgent: generating improved content")

        # 1. Get similar repo examples
        examples = self.web_search.search_similar_repos(readme, top_k=3)

        # 2. Get RAG suggestions
        rag_hints = self.rag.retrieve(readme)

        # 3. Synthesize improved README
        # We inject RAG hints into the readme for the prompt context
        context_readme = readme + \
            "\n\n<!-- BEST PRACTICES SUGGESTIONS -->\n" + "\n".join(rag_hints)
        improved = self.web_search.summarize_and_improve(
            context_readme, examples)

        # 4. Suggest images
        suggestions = {
            "architecture_diagram": "Diagram showing data flow and model components.",
            "demo_screenshot": "CLI/UI usage example image with sample output."
        }

        improvement = ContentImprovement(
            improved_readme=improved, suggested_images=suggestions)
        return improvement
