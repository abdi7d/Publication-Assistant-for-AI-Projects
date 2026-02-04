# tools/web_search.py
import os
import logging
from typing import List, Dict, Any
try:
    from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
except Exception:
    DuckDuckGoSearchAPIWrapper = None
try:
    from google import genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)

_genai_client = None

# Configure Gemini if key is present (should be loaded from .env in main/app)
if os.getenv("GOOGLE_API_KEY") and genai is not None:
    try:
        _genai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    except Exception:
        pass


class WebSearchTool:
    def __init__(self):
        # graceful fallbacks if dependencies missing
        self.search = None
        if DuckDuckGoSearchAPIWrapper is not None:
            try:
                self.search = DuckDuckGoSearchAPIWrapper()
            except Exception:
                self.search = None
        self.model = None
        if genai is not None and os.getenv("GOOGLE_API_KEY"):
            try:
                self.model = _genai_client
            except Exception:
                self.model = None

    def search_similar_repos(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Searches for similar repositories or articles using DuckDuckGo.
        """
        logger.info(f"Searching web for: {query}")
        try:
            # DuckDuckGo search
            if self.search is None:
                logger.warning(
                    "DuckDuckGoSearchAPIWrapper unavailable; returning empty results.")
                return []
            results = self.search.results(query, max_results=top_k)
            # Standardize output
            clean_results = []
            for res in results:
                clean_results.append({
                    "title": res.get("title", "No Title"),
                    "link": res.get("link", ""),
                    "snippet": res.get("snippet", "")
                })
            return clean_results
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def summarize_and_improve(self, readme: str, examples: List[Dict]) -> str:
        """
        Uses Gemini to suggest improvements based on the current README and found examples.
        """
        example_text = "\n\n".join(
            [f"Example ({e['title']}): {e['snippet']}" for e in examples])

        prompt = f"""
        You are an expert developer advocate. 
        Your task is to suggest improvements for a GitHub repository README.
        
        Current README content:
        {readme[:4000]} # Truncated to avoid token limits if very long
        
        Relevant search results for similar successful projects:
        {example_text}
        
        Based on the above, rewrite the README to be more engaging, clear, and professional. 
        Focus on:
        1. Clear Value Prop
        2. Easy Installation/Usage
        3. Professional Tone
        
        Output ONLY the improved README markdown.
        """

        try:
            if self.model is None:
                logger.warning(
                    "Gemini model unavailable; returning simple heuristic improvement.")
                # simple heuristic improvement
                lines = readme.splitlines()
                title = lines[0] if lines else "Project"
                return f"# {title}\n\nImproved summary: This project implements X. Add Installation and Usage sections."
            response = self.model.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return "Error generating improvement suggestions."
