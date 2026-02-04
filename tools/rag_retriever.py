# tools/rag_retriever.py
import os
import logging
import uuid
from typing import List
try:
    import chromadb
    from chromadb.config import Settings
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
        self.embed_model = 'models/embedding-001'
        
        # Ensure we have dependencies
        if chromadb is None:
            logger.warning("chromadb not installed. RAG functionality disabled.")
            return

        try:
            # Use a persistent client with a specific path
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection("project_suggestions")
            
            # Check if empty, then seed
            if self.collection.count() == 0:
                self.seed_knowledge_base()
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            self.client = None
            self.collection = None

    def seed_knowledge_base(self):
        sample_docs = [
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
        
        if self.collection is None:
            return

        if genai is None or not os.getenv("GOOGLE_API_KEY"):
            logger.warning("RAG seed skipped: missing genai or API key.")
            return

        try:
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            for doc in sample_docs:
                embedding = client.models.embed_content(
                    model=self.embed_model,
                    contents=doc
                ).embedding
                self.collection.add(
                    ids=[str(uuid.uuid4())],
                    embeddings=[embedding],
                    documents=[doc]
                )
            logger.info("Seeded RAG knowledge base with %d items.", len(sample_docs))
        except Exception as e:
            logger.error(f"Error seeding RAG: {e}")

    def retrieve(self, text: str, top_k: int = 3) -> List[str]:
        """
        Retrieves relevant suggestions based on the input text.
        """
        if not text:
            return []
            
        if self.collection is None:
            logger.warning("RAG retrieve called but collection is not initialized.")
            return []

        if genai is None or not os.getenv("GOOGLE_API_KEY"):
            logger.warning("RAG retrieve skipped: missing genai or API key.")
            return []

        try:
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            # Generate embedding for query
            query_embedding = client.models.embed_content(
                model=self.embed_model,
                contents=text[:1000]
            ).embedding
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            if results and results['documents']:
                # Flatten the list of lists
                return [doc for sublist in results['documents'] for doc in sublist]
            return []
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return []
