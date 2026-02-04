# tools/repo_parser.py
import os
import zipfile
import shutil
import subprocess
import tempfile
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class RepoParser:
    """
    Parse a local repository path, a zipped repository, or a remote git URL.
    Methods:
      - parse(repo_source: str) -> dict with keys: files (dict fname->content), README.md if present
    Supports:
      - local directory path
      - zip file path
      - remote git URL
    """
    def parse(self, repo_source: str) -> Dict[str, Any]:
        if os.path.exists(repo_source):
            if os.path.isdir(repo_source):
                return self._parse_dir(repo_source)
            elif repo_source.endswith(".zip"):
                return self._parse_zip(repo_source)
        elif repo_source.startswith("http") or repo_source.startswith("git@"):
            return self._parse_git(repo_source)
        
        raise ValueError(f"Invalid repo_source: {repo_source}. Must be a local path, zip file, or git URL.")

    def _parse_dir(self, path: str) -> Dict[str, Any]:
        files = {}
        readme = ""
        # Ignore common heavy directories
        ignore_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", ".idea", ".vscode"}
        
        for root, dirs, filenames in os.walk(path):
            # Modify dirs in-place to prune traversal
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for fname in filenames:
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, path)
                try:
                    # Skip binary or very large files
                    if os.path.getsize(full) > 100_000: # 100KB limit for analysis
                        continue
                        
                    with open(full, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    files[rel] = content
                    if fname.lower().startswith("readme"):
                        readme = content
                except Exception as e:
                    logger.warning("Failed to read file %s: %s", full, e)
        return {"files": files, "README.md": readme}

    def _parse_zip(self, zip_path: str) -> Dict[str, Any]:
        files = {}
        readme = ""
        with zipfile.ZipFile(zip_path, "r") as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                with z.open(info) as f:
                    try:
                        content = f.read().decode("utf-8", errors="ignore")
                        files[info.filename] = content
                        if os.path.basename(info.filename).lower().startswith("readme"):
                            readme = content
                    except Exception as e:
                        logger.warning("Failed to decode %s: %s", info.filename, e)
        return {"files": files, "README.md": readme}

    def _parse_git(self, git_url: str) -> Dict[str, Any]:
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Cloning {git_url} to {temp_dir}")
        try:
            subprocess.check_call(["git", "clone", "--depth", "1", git_url, temp_dir])
            return self._parse_dir(temp_dir)
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e}")
            raise RuntimeError(f"Failed to clone repository: {git_url}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
