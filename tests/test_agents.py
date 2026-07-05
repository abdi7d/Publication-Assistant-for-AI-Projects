# tests/test_agents.py
import tempfile
import os
from tools.repo_parser import RepoParser
from tools.keyword_extractor import KeywordExtractor
from agents.repo_analyzer import RepoAnalyzerAgent
from agents.metadata_recommender import MetadataRecommenderAgent
from tools.rag_retriever import RAGRetriever
from orchestration.graph import Orchestrator


def create_tmp_repo(tmpdir):
    p = tmpdir.mkdir("repo")
    (p.join("README.md")).write(
        "Project Title\n\nThis project uses a neural network and dataset X.\n\nUsage: python run.py")
    (p.join("run.py")).write("print('hello world')")
    return str(p)


def test_repo_parser_and_analyzer(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    readme_file = repo_dir / "README.md"
    readme_file.write_text("Sample Project\n\nThis is an example.")
    run_file = repo_dir / "run.py"
    run_file.write_text("print('hi')")
    parser = RepoParser()
    parsed = parser.parse(str(repo_dir))
    assert "README.md" in parsed and parsed["README.md"] is not None
    analyzer = RepoAnalyzerAgent(repo_source=str(repo_dir), repo_parser=parser)
    analysis = analyzer.run()
    assert analysis.code_stats["file_count"] >= 1


def test_metadata_recommender(tmp_path):
    ke = KeywordExtractor()
    mr = MetadataRecommenderAgent(keyword_extractor=ke)
    rec = mr.run(
        "This project demonstrates image classification using CNN and PyTorch.", {})
    assert len(rec.tags) > 0
    assert len(rec.title_suggestions) >= 1


def test_rag_retriever_falls_back_without_chromadb(monkeypatch):
    monkeypatch.setenv("PUBLISH_ASSIST_DISABLE_RAG", "1")
    retriever = RAGRetriever(db_path="unused")
    assert retriever.is_available is False
    results = retriever.retrieve("installation instructions")
    assert len(results) > 0


def test_orchestrator_includes_evaluation_summary():
    class FakeRepoAnalyzer:
        def run(self):
            return type("Analysis", (), {
                "readme": "# Demo\n\nInstall with pip.",
                "files": {"README.md": "# Demo"},
                "code_stats": {"total_lines": 25},
                "missing_sections": []
            })()

    class FakeMetadataRecommender:
        def run(self, readme_text, code_files):
            return type("Metadata", (), {
                "title_suggestions": ["Demo Project"],
                "tags": ["python", "demo"],
                "short_description": "A demo project"
            })()

    class FakeContentImprover:
        def run(self, readme, metadata, style="Technical Blog", goal=""):
            return type("Content", (), {"improved_readme": "# Demo"})()

    class FakeReviewer:
        def run(self, readme, code_stats):
            return type("Review", (), {"score": 8.0, "issues": [], "strengths": [], "recommendations": []})()

    class FakeFactChecker:
        def run(self, readme_text):
            return type("FactCheck", (), {"claims_found": [], "verified": [], "flagged": []})()

    agents = {
        "repo_analyzer": FakeRepoAnalyzer(),
        "metadata_recommender": FakeMetadataRecommender(),
        "content_improver": FakeContentImprover(),
        "reviewer_critic": FakeReviewer(),
        "fact_checker": FakeFactChecker(),
    }

    result = Orchestrator().run_pipeline(agents, "./demo_repo")

    assert "evaluation" in result
    assert result["evaluation"]["mock_score"] >= 0.0
