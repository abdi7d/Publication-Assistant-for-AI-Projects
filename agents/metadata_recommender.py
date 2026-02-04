# agents/metadata_recommender.py
from dataclasses import dataclass
from typing import List, Dict
from tools.keyword_extractor import KeywordExtractor
import logging
try:
    from google import genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)


@dataclass
class MetadataRecommendation:
    title_suggestions: List[str]
    tags: List[str]
    short_description: str


class MetadataRecommenderAgent:
    """
    Suggest metadata (title, tags, short description) for the repository based on README and code.
    """

    def __init__(self, keyword_extractor: KeywordExtractor):
        self.keyword_extractor = keyword_extractor
        # lazy model: only create if genai is available
        self.model = None
        if genai is not None:
            try:
                self.model = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            except Exception:
                self.model = None

    def run(self, readme_text: str, code_files: dict) -> MetadataRecommendation:
        logger.info("MetadataRecommenderAgent: extracting keywords")

        # Extract keywords
        keywords = self.keyword_extractor.extract(readme_text)

        # Use simple heuristics or LLM for title generation
        title_suggestions = self._make_titles(readme_text, keywords)

        # Generate description using Gemini
        short_desc = self._generate_description(readme_text, keywords)

        rec = MetadataRecommendation(
            title_suggestions=title_suggestions,
            tags=keywords[:12],
            short_description=short_desc
        )
        return rec

    def _make_titles(self, readme: str, keywords: List[str]) -> List[str]:
        if not self.model or not keywords:
            base = " ".join(keywords[:2]).title() if keywords else "Project"
            return [f"{base} Tool", f"Advanced {base}", f"{base} Implementation"]

        prompt = f"""
        Generate 3 catchy, professional titles for an AI/Software project based on these keywords and snippet.
        Keywords: {", ".join(keywords[:5])}
        Snippet: {readme[:500]}
        
        Return commas separated list.
        """
        try:
            response = self.model.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            return [t.strip() for t in response.text.split(",") if t.strip()]
        except Exception:
            base = " ".join(keywords[:3]).title()
            return [f"{base} Project", f"Advanced {base}", f"{base} Implementation"]

    def _generate_description(self, readme: str, keywords: List[str]) -> str:
        if not self.model:
            return f"A software project demonstrating {', '.join(keywords[:3])}."

        prompt = f"""
        Write a one-sentence, high-impact description (max 200 chars) for this project.
        Keywords: {", ".join(keywords[:5])}
        Readme start: {readme[:500]}
        """
        try:
            response = self.model.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            desc = response.text.replace("\n", " ").strip()
            return desc if len(desc) < 250 else desc[:247] + "..."
        except Exception:
            return "A software project utilizing " + ", ".join(keywords[:3])
