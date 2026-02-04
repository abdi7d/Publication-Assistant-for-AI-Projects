# tests/test_agents.py
import tempfile
import os
from tools.repo_parser import RepoParser
from tools.keyword_extractor import KeywordExtractor
from agents.repo_analyzer import RepoAnalyzerAgent
from agents.metadata_recommender import MetadataRecommenderAgent


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
