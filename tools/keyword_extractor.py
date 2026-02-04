# tools/keyword_extractor.py
import logging
import os
import re
from typing import List
try:
    from google import genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)


class KeywordExtractor:
    def __init__(self, top_k: int = 10):
        self.top_k = top_k
        self.model = None
        
        # Check for API key and library presence
        if genai is not None and os.getenv("GOOGLE_API_KEY"):
            try:
                self.model = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini model: {e}")
                self.model = None

    def extract(self, text: str) -> List[str]:
        """
        Extracts high-quality keywords using Gemini LLM or fallback heuristics.
        """
        if not text:
            return []

        # LLM Approach
        if self.model:
            prompt = f"""
            Extract the top {self.top_k} most relevant technical keywords, topics, and libraries from the following text.
            Return ONLY a comma-separated list of keywords. NO formatting, no bullets, no introduction.
            
            Text:
            {text[:3000]}
            """
            try:
                response = self.model.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt
                )
                keywords = [k.strip() for k in response.text.split(",") if k.strip()]
                logger.debug("KeywordExtractor (LLM): extracted keywords: %s", keywords)
                return keywords[:self.top_k]
            except Exception as e:
                logger.error("Keyword extraction (LLM) error: %s", e)
        
        # Fallback Heuristic
        return self._heuristic_extract(text)

    def _heuristic_extract(self, text: str) -> List[str]:
        """
        Simple frequency-based keyword extraction fallback.
        """
        logger.info("KeywordExtractor: using heuristic fallback")
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        stopwords = {"the", "and", "for", "with", "this", "that", "from", "your", "have", "are", "can", "use"}
        
        freq = {}
        for w in words:
            if w not in stopwords:
                freq[w] = freq.get(w, 0) + 1
        
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:self.top_k]]
