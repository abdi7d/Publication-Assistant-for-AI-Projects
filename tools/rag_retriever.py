# tools/rag_retriever.py
import logging
import os
import re
import shutil
import uuid
from typing import List

try:
    import chromadb
except Exception:
    chromadb = None
try:
    from google import genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)


class RAGRetriever:
    def __init__(self, db_path: str = "./chroma_db"):
        self.client = None
        self.collection = None
        self.embed_model = "models/gemini-embedding-001"
        self.is_available = False
        self._fallback_documents = self._default_documents()

        if os.getenv("PUBLISH_ASSIST_DISABLE_RAG", "").lower() in {"1", "true", "yes"}:
            logger.info(
                "RAG disabled by environment setting; using local fallback retrieval.")
            return

        if os.getenv("PUBLISH_ASSIST_ENABLE_RAG", "").lower() not in {"1", "true", "yes"}:
            logger.info(
                "RAG disabled by default; using local fallback retrieval to avoid ChromaDB startup issues.")
            return

        if chromadb is None:
            logger.warning(
                "chromadb not installed. RAG functionality disabled.")
            return

        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(
                "project_suggestions")
            self.is_available = True

            if self.collection.count() == 0:
                self.seed_knowledge_base()
        except BaseException as e:
            logger.warning(
                "Failed to initialize ChromaDB-backed RAG system: %s", e)
            self._safe_cleanup_db_path(db_path)
            self.client = None
            self.collection = None
            self.is_available = False

    def _safe_cleanup_db_path(self, db_path: str) -> None:
        try:
            if db_path and os.path.exists(db_path):
                shutil.rmtree(db_path, ignore_errors=True)
        except Exception:
            pass

    def _default_documents(self) -> List[str]:
        return [
            "Add clear installation instructions with 'pip install -r requirements.txt'.",
            "Include usage examples with code snippets in the README.",
            "Suggest adding diagrams for architecture visualization (Mermaid or images).",
            "Recommend adding a License file (MIT, Apache 2.0).",
            "Include a Contributing guide (CONTRIBUTING.md).",
            "Add badges for build status, license, and python version.",
            "Structure the project with clearly defined folders: agents, tools, utils.",
            "Add unit tests using pytest in a 'tests/' directory.",
            "Provide a 'Quick Start' section for immediate gratification.",
            "List all dependencies clearly in requirements.txt or pyproject.toml."
        ]

    def seed_knowledge_base(self):
        if self.collection is None:
            return

        if genai is None or not os.getenv("GOOGLE_API_KEY"):
            logger.warning("RAG seed skipped: missing genai or API key.")
            return

        try:
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            for doc in self._fallback_documents:
                embedding = client.models.embed_content(
                    model=self.embed_model,
                    contents=doc
                ).embedding
                self.collection.add(
                    ids=[str(uuid.uuid4())],
                    embeddings=[embedding],
                    documents=[doc]
                )
            logger.info("Seeded RAG knowledge base with %d items.",
                        len(self._fallback_documents))
        except Exception as e:
            logger.error("Error seeding RAG: %s", e)

    def retrieve(self, text: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant suggestions using ChromaDB when available, otherwise a local fallback."""
        if not text:
            return []

        if self.collection is not None and self.is_available:
            if genai is None or not os.getenv("GOOGLE_API_KEY"):
                logger.warning(
                    "RAG retrieve skipped: missing genai or API key.")
                return self._fallback_retrieve(text, top_k)

            try:
                client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
                query_embedding = client.models.embed_content(
                    model=self.embed_model,
                    contents=text[:1000]
                ).embedding

                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )

                if results and results.get("documents"):
                    return [doc for sublist in results["documents"] for doc in sublist]
            except Exception as e:
                logger.warning("RAG retrieval error: %s", e)

        return self._fallback_retrieve(text, top_k)

    def _fallback_retrieve(self, text: str, top_k: int = 3) -> List[str]:
        query_terms = set(re.findall(r"[a-zA-Z0-9]+", text.lower()))
        ranked = []
        for doc in self._fallback_documents:
            doc_terms = set(re.findall(r"[a-zA-Z0-9]+", doc.lower()))
            overlap = len(query_terms & doc_terms)
            if overlap:
                ranked.append((overlap, doc))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [doc for _, doc in ranked[:top_k]]
