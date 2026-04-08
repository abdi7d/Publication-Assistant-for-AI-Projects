from tools.arxiv_scholar import ArxivScholarTool
from tools.rag_retriever import RAGRetriever
from tools.keyword_extractor import KeywordExtractor
from tools.web_search import WebSearchTool
from tools.repo_parser import RepoParser
from agents.fact_checker import FactCheckerAgent
from agents.reviewer_critic import ReviewerCriticAgent
from agents.content_improver import ContentImproverAgent
from agents.metadata_recommender import MetadataRecommenderAgent
from agents.repo_analyzer import RepoAnalyzerAgent
from orchestration.graph import Orchestrator
import gradio as gr
import logging
import os
import tempfile
import json
import re
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# --- Core Component Imports ---


# --- Setup ---
# Empty line here to maintain spacing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Projects persistence file
PROJECTS_FILE = Path("projects.json")


def load_projects():
    if not PROJECTS_FILE.exists():
        return {}
    try:
        with PROJECTS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_project(project_id: str, repo_url: str, metadata: dict = None):
    projects = load_projects()
    projects[project_id] = {"repo_url": repo_url, "metadata": metadata or {}}
    with PROJECTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2)
    return list(projects.keys())


def slugify(text: str) -> str:
    text = text or "project"
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    if not text:
        return "project"
    return text


def delete_project(project_id: str):
    projects = load_projects()
    if project_id in projects:
        projects.pop(project_id)
        with PROJECTS_FILE.open("w", encoding="utf-8") as f:
            json.dump(projects, f, indent=2)
    return list(projects.keys())


def render_tags_as_html(tags: list) -> str:
    """Renders a list of tags as interactive-looking HTML pill badges."""
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"]
    html = '<div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0;">'
    for i, tag in enumerate(tags[:10]):
        color = colors[i % len(colors)]
        html += f'<span style="background-color: {color}22; color: {color}; border: 1px solid {color}44; border-radius: 16px; padding: 4px 12px; font-size: 14px; font-weight: 500; font-family: sans-serif;">{tag}</span>'
    html += '</div>'
    return html

# --- Logic Functions ---


def validate_repo_logic(repo_url):
    """Handles the repo validation for the UI button."""
    if not repo_url:
        return "⚠️ Please enter a repository URL.", ""

    parser = RepoParser()
    try:
        result = parser.parse(repo_url)
        files = list(result.get("files", {}).keys())[:20]
        tree = "\n".join([f"📄 {f}" for f in files])
        return "✅ Repository validated successfully.", tree
    except Exception as e:
        logger.warning("Validation failed, trying fallback: %s", e)
        try:
            temp_dir = tempfile.mkdtemp(prefix="fallback_")
            with open(os.path.join(temp_dir, "README.md"), "w") as f:
                f.write(
                    "# Fallback Project\nRemote clone failed, showing local structure.")
            result = parser.parse(temp_dir)
            files = list(result.get("files", {}).keys())
            tree = "\n".join([f"📄 {f}" for f in files])
            return f"ℹ️ Remote clone failed. Using offline sample fallback.", tree
        except:
            return f"❌ Validation Error: {str(e)}", ""


def generate_full_article(repo_url, style, length, model, goal, project_desc, provider=None):
    """The main generation pipeline triggered by the 'Generate' button."""
    if not repo_url:
        return "Error", "Error", "Please provide a URL", "The URL is missing."

    try:
        # Instantiate Tools & Agents
        parser, kw, rag = RepoParser(), KeywordExtractor(), RAGRetriever()
        web = WebSearchTool(selected_model=model, provider=provider)
        scholar = ArxivScholarTool()
        agents = {
            "repo_analyzer": RepoAnalyzerAgent(repo_url, parser),
            "metadata_recommender": MetadataRecommenderAgent(kw),
            "content_improver": ContentImproverAgent(web, rag),
            "reviewer_critic": ReviewerCriticAgent(),
            "fact_checker": FactCheckerAgent(scholar),
        }

        # Run Pipeline
        orch = Orchestrator()
        result = orch.run_pipeline(agents, repo_url, style=style, goal=goal)

        analysis = result.get("analysis")
        metadata = result.get("metadata")
        content_impr = result.get("content_improvement")

        # Formatting Output
        title = getattr(metadata, 'title_suggestions', ["Untitled Project"])[0]
        subtitle = getattr(metadata, 'short_description',
                           project_desc or "Analysis Result")
        tags = getattr(metadata, 'tags', ["AI", "Research"])

        # Render tags as HTML pill badges (only once, at the top)
        tags_html = render_tags_as_html(tags)

        # Build structured body: only one title, add 'Project Tags' subtitle above tags, and ensure tags are not repeated in the body
        # Compose output: title, 'Project Tags' subtitle, tags, then cleaned body
        out_title = f"# {title}"
        out_tags = '<div style="margin-top: 10px; margin-bottom: 2px; font-weight: bold; font-size: 18px;">Project Tags</div>' + tags_html
        improved_readme = getattr(
            content_impr, 'improved_readme', "No improvements generated.")

        # Remove any top-level title and tags section from improved_readme
        import re
        lines = improved_readme.splitlines()
        cleaned_lines = []
        skip = True
        for i, line in enumerate(lines):
            # Skip initial title (lines starting with # or ## at the very top)
            if skip and (re.match(r'^\s*#{1,3} ', line) or re.match(r'^\s*Project Tags', line, re.IGNORECASE) or re.match(r'^\s*<div.*?>.*?</div>', line)):
                continue
            # Skip badge/tag lines (HTML or markdown) immediately after title
            if skip and (re.match(r'^\s*<span|^\s*<div|^\s*#\w+', line)):
                continue
            # Once we hit a non-title/tag line, stop skipping
            if skip and line.strip() and not (re.match(r'^\s*#{1,3} ', line) or re.match(r'^\s*Project Tags', line, re.IGNORECASE) or re.match(r'^\s*<div.*?>.*?</div>', line) or re.match(r'^\s*<span|^\s*#\w+', line)):
                skip = False
            if not skip:
                cleaned_lines.append(line)
        body = '\n'.join(cleaned_lines).lstrip(
            '\n') or "No improvements generated."

        # Only return one title, then tags, then body (no subtitle)
        return out_title, "", out_tags, body

    except Exception as e:
        logger.exception("Generation failed")
        return "Error", "Error", "", f"Pipeline failed: {str(e)}"


# --- Gradio UI (CSS removed; using a soft theme and simple Markdown for styling) ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:

    with gr.Row():
        # --- LEFT SIDEBAR (Config Area) ---
        with gr.Column(scale=1):
            gr.Markdown("## ⚙️ Configuration")

            gr.Markdown("### 📖 Writing Style")
            style_input = gr.Dropdown(
                ["Technical Blog", "Academic Showcase",
                    "Executive Summary", "User Guide"],
                value="Technical Blog", label="Choose preferred style"
            )

            gr.Markdown("### 📏 Publication Length")
            length_input = gr.Radio(
                ["Short", "Medium", "Long"], value="Medium", label="Target length")

            gr.Markdown("### 🤖 AI Model")
            model_input = gr.Dropdown(
                [
                    "Gemini 1.5 Flash Latest (Google)",
                    "Gemini 1.0 Pro (Google)",
                    "Groq Llama-3.1-8B-Instant (Groq)",
                    "Groq Mixtral-8x7B-32768 (Groq)",
                    "Heuristic Fallback (No LLM)"
                ],
                value="Gemini 1.5 Flash Latest (Google)", label="Choose LLM"
            )

        # --- RIGHT MAIN PANEL ---
        with gr.Column(scale=4):
            # Header using Markdown (relies on theme for colors)
            gr.Markdown("""
# 📝 Publication Assistant for AI Projects
*Transform your GitHub repository into a polished article or README.*
""")

            # Project Selection Row
            projects = load_projects()
            existing_choices = list(projects.keys())
            show_existing = len(existing_choices) > 0

            with gr.Row():
                with gr.Column(scale=2):
                    proj_mode = gr.Dropdown(
                        ["Create New Project", "Use Existing Project"],
                        value="Create New Project",
                        label="📂 Project Mode"
                    )
                with gr.Column(scale=3):
                    proj_id = gr.Textbox(
                        placeholder="Enter New Project ID (optional)", label="New Project ID")

            # Existing project selector (hidden unless mode set to use existing)
            existing_proj_dropdown = gr.Dropdown(
                choices=existing_choices,
                value="",
                visible=show_existing,
                label="Select Existing Project",
                allow_custom_value=True,
            )
            delete_btn = gr.Button(
                "Delete Project", variant="danger", visible=show_existing)

            with gr.Tabs() as tabs:

                # Tab 1: Project Setup
                with gr.TabItem("🔧 Project Setup"):
                    gr.Markdown("#### 📁 Repository URL")
                    with gr.Row():
                        repo_url_input = gr.Textbox(
                            placeholder="https://github.com/user/repo", scale=4, container=False)
                        validate_btn = gr.Button(
                            "🔍 Validate", scale=1, variant="secondary")

                    val_msg = gr.Markdown(visible=False)
                    tree_viewer = gr.Code(
                        label="Repo Structure", language="markdown", lines=6)

                    gr.Markdown("#### 📋 Project Description (Optional)")
                    desc_input = gr.Textbox(
                        lines=3, placeholder="Describe the core purpose of your project...", show_label=False)

                    gr.Markdown("#### 📄 Supplemental Documents")
                    gr.File(label="Upload PDFs or Docs for context",
                            file_count="multiple")

                # Tab 2: Generation
                with gr.TabItem("🚀 Generation"):
                    gr.Markdown("#### 🎯 Generation Goal")
                    goal_input = gr.Textbox(
                        placeholder="e.g. Focus on the architecture and the 'Fake Information Replacement' module.",
                        # placeholder="e.g. Write an article about this project and make sure to mention the fake information replacement module.",
                        lines=3, show_label=False
                    )

                    generate_btn = gr.Button(
                        "🚀 Generate Article", variant="primary")

                    with gr.Column(visible=False) as output_container:
                        gr.Markdown("---")
                        out_title = gr.Markdown()
                        out_sub = gr.Markdown()
                        out_tags = gr.HTML()  # Changed to HTML for pill badges
                        out_body = gr.Markdown()

    # --- Event Handling ---
    def on_validate(url, mode, existing_sel):
        # If using an existing project, override url with stored repo_url
        if mode == "Use Existing Project" and existing_sel:
            projects = load_projects()
            proj = projects.get(existing_sel)
            if proj:
                url = proj.get("repo_url", url)
        msg, tree = validate_repo_logic(url)
        return gr.update(value=msg, visible=True), tree

    validate_btn.click(on_validate, inputs=[
                       repo_url_input, proj_mode, existing_proj_dropdown], outputs=[val_msg, tree_viewer])

    def on_generate(url, style, length, model, goal, desc, mode, existing_sel, new_id):
        # Map UI model selection to provider/model
        model_map = {
            "Gemini 1.5 Flash Latest (Google)": ("google", "gemini-1.5-flash-latest"),
            "Gemini 1.0 Pro (Google)": ("google", "gemini-1.0-pro"),
            "Groq Llama-3.1-8B-Instant (Groq)": ("groq", "llama-3.1-8b-instant"),
            "Groq Mixtral-8x7B-32768 (Groq)": ("groq", "mixtral-8x7b-32768"),
            "Heuristic Fallback (No LLM)": ("none", "heuristic")
        }
        provider, model_id = model_map.get(
            model, ("google", "gemini-1.5-flash-latest"))

        # Resolve repo URL depending on project mode
        projects = load_projects()
        final_url = url
        project_id_to_save = None
        if mode == "Use Existing Project" and existing_sel:
            proj = projects.get(existing_sel)
            if not proj:
                # try case-insensitive exact match
                for k, v in projects.items():
                    if k.lower() == (existing_sel or "").lower():
                        proj = v
                        existing_sel = k
                        break
            if not proj:
                # try substring match
                for k, v in projects.items():
                    if existing_sel and existing_sel.lower() in k.lower():
                        proj = v
                        existing_sel = k
                        break
            if proj:
                final_url = proj.get("repo_url", url)
                project_id_to_save = existing_sel
        else:
            # Create new project: pick provided id or generate from repo URL
            project_id_to_save = new_id.strip() if new_id and new_id.strip() else slugify(final_url)

        title, sub, tags, body = generate_full_article(
            final_url, style, length, model_id, goal, desc, provider)

        # If we created a new project, persist it
        if mode != "Use Existing Project" and project_id_to_save:
            try:
                save_project(project_id_to_save, final_url, {"title": title})
            except Exception:
                logger.exception("Failed to save project")

        # After potential save, refresh choices
        updated_choices = list(load_projects().keys())
        return gr.update(visible=True), title, sub, tags, body, gr.update(choices=updated_choices, value=project_id_to_save or "", visible=len(updated_choices) > 0)

    generate_btn.click(
        on_generate,
        inputs=[repo_url_input, style_input, length_input, model_input,
                goal_input, desc_input, proj_mode, existing_proj_dropdown, proj_id],
        outputs=[output_container, out_title, out_sub,
                 out_tags, out_body, existing_proj_dropdown]
    )

    # Update UI visibility when project mode changes
    def on_mode_change(mode):
        projects = load_projects()
        has_existing = len(projects) > 0
        if mode == "Use Existing Project":
            return gr.update(visible=has_existing, value=""), gr.update(visible=False, value=""), gr.update(value="", interactive=False), gr.update(value="Using existing project. Select one from dropdown.", visible=True)
        else:
            # Create New: clear existing selection and enable repo input
            return gr.update(visible=False, value=""), gr.update(visible=True, value=""), gr.update(interactive=True, value=""), gr.update(value="", visible=False)

    proj_mode.change(on_mode_change, inputs=[proj_mode], outputs=[
                     existing_proj_dropdown, proj_id, repo_url_input, val_msg])

    # When an existing project is selected, autofill repo_url and new project id field
    def on_existing_select(selected):
        if not selected:
            return gr.update(value=""), gr.update(value=""), gr.update(value="No project selected.", visible=True)
        projects = load_projects()
        proj = projects.get(selected)
        if not proj:
            # try to find a match
            for k, v in projects.items():
                if k.lower() == selected.lower() or (selected.lower() in k.lower()):
                    proj = v
                    selected = k
                    break
        repo = proj.get("repo_url", "") if proj else ""
        return gr.update(value=repo, interactive=False), gr.update(value=selected), gr.update(value=f"Using existing project: {selected}", visible=True)

    existing_proj_dropdown.change(on_existing_select, inputs=[
                                  existing_proj_dropdown], outputs=[repo_url_input, proj_id, val_msg])

    # Delete project callback
    def on_delete(selected):
        if not selected:
            return gr.update(visible=False, choices=list(load_projects().keys())), gr.update(value=""), gr.update(value=""), gr.update(value="No project selected.")
        updated = delete_project(selected)
        return gr.update(choices=updated, value="", visible=len(updated) > 0), gr.update(value=""), gr.update(value=""), gr.update(value=f"Deleted project '{selected}'.")

    delete_btn.click(on_delete, inputs=[existing_proj_dropdown], outputs=[
                     existing_proj_dropdown, repo_url_input, proj_id, val_msg])

# --- Launch ---
if __name__ == "__main__":
    demo.launch()
