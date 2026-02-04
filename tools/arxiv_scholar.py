# tools/arxiv_scholar.py
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    import arxiv  # type: ignore
    _HAS_ARXIV = True
except Exception:
    arxiv = None  # type: ignore
    _HAS_ARXIV = False
    logger.warning(
        "Optional dependency 'arxiv' not installed. ArxivScholarTool will return empty results.")


class ArxivScholarTool:
    def __init__(self, rate_limit: float = 0.3):
        self.rate_limit = rate_limit
        if _HAS_ARXIV:
            try:
                self.client = arxiv.Client()
            except Exception:
                self.client = None
                logger.exception(
                    "Failed to initialize arxiv.Client; arXiv lookups disabled.")
        else:
            self.client = None

    def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search arXiv for papers related to the query.

        If the `arxiv` package is not available or initialization failed,
        this returns an empty list so the rest of the pipeline can proceed.
        """
        logger.info("ArxivScholarTool: searching for: %s", query)
        if not _HAS_ARXIV or self.client is None:
            logger.debug(
                "ArxivScholarTool: arxiv not available, returning empty list")
            return []

        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            results = []
            for result in self.client.results(search):
                results.append(
                    {
                        "title": result.title,
                        "summary": result.summary.replace("\n", " "),
                        "id": result.entry_id,
                        "pdf_url": result.pdf_url,
                        "published": str(result.published),
                    }
                )
            return results
        except Exception as e:
            logger.exception("Arxiv query error: %s", e)
            return []
