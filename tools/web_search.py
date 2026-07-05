# tools/web_search.py
import os
import logging
from typing import List, Dict, Any
try:
    from langchain_community.tools.tavily_search import TavilySearchResults
except Exception:
    TavilySearchResults = None

try:
    from google import genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)


class WebSearchTool:
    def __init__(self, selected_model: str = None, provider: str = None):
        # graceful fallbacks if dependencies missing
        self.search = None
        tavily_key = os.getenv("TAVILY_API_KEY")
        if TavilySearchResults is not None and tavily_key:
            try:
                self.search = TavilySearchResults(max_results=5)
                logger.info("WebSearchTool: Tavily search tool initialized.")
            except Exception as e:
                logger.error(
                    f"WebSearchTool: Tavily initialization failed: {e}")
                self.search = None
        else:
            logger.warning(
                f"WebSearchTool: Tavily tool NOT initialized. Key missing: {not tavily_key}")

        self.model = None
        self.selected_model = selected_model or "gemini-1.5-flash"
        self.provider = provider or "google"
        self.gemini_client = None
        self.groq_client = None
        self.active_client = None
        # Try to initialize both clients if possible
        google_api_key = os.getenv("GOOGLE_API_KEY")
        groq_api_key = os.getenv("GROQ_API_KEY")
        # Gemini (Google)
        if genai is not None and google_api_key:
            try:
                self.gemini_client = genai.Client(api_key=google_api_key)
                logger.info(
                    "WebSearchTool: Gemini client successfully initialized.")
            except Exception as e:
                logger.error(
                    f"WebSearchTool: Gemini client initialization failed: {e}")
                self.gemini_client = None
        # Groq (Llama)
        try:
            from groq import Groq
            if groq_api_key:
                self.groq_client = Groq(api_key=groq_api_key)
                logger.info(
                    "WebSearchTool: Groq client successfully initialized.")
        except Exception as e:
            logger.warning(
                f"WebSearchTool: Groq client initialization failed: {e}")
            self.groq_client = None

        # Set active client based on provider, fallback if needed
        if self.provider == "google":
            self.active_client = self.gemini_client or self.groq_client
        elif self.provider == "groq":
            self.active_client = self.groq_client or self.gemini_client
        else:
            self.active_client = self.gemini_client or self.groq_client

    def search_similar_repos(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Searches for similar repositories or articles using Tavily.
        """
        logger.info(f"Searching web with Tavily for: {query}")
        try:
            if self.search is None:
                logger.warning(
                    "Tavily search tool unavailable; returning empty results.")
                return []

            # TavilySearchResults.run returns a list of dictionaries
            # We use invoke which is standard for LangChain tools
            results = self.search.invoke(query)

            # Ensure results is a list of dicts
            if isinstance(results, str):
                logger.warning(
                    f"Tavily returned a string instead of a list: {results[:100]}...")
                return []

            if not isinstance(results, list):
                logger.warning(
                    f"Tavily returned unexpected type: {type(results)}")
                return []

            # Standardize output
            clean_results = []
            for res in results[:top_k]:
                if not isinstance(res, dict):
                    continue
                clean_results.append({
                    "title": res.get("title", "No Title"),
                    "link": res.get("url", ""),  # Tavily uses 'url'
                    "snippet": res.get("content", "")  # Tavily uses 'content'
                })
            return clean_results
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []

    def summarize_and_improve(self, readme: str, examples: List[Dict], style: str = "Technical Blog", goal: str = "") -> str:
        """
        Uses Gemini to suggest improvements based on the current README, found examples, and user goal.
        """
        logger.info(f"summarize_and_improve: Style={style}, Goal={goal}")

        example_text = ""
        if examples:
            example_text = "\n\n".join(
                [f"Example ({e['title']}): {e['snippet']}" for e in examples if isinstance(e, dict)])

        prompt = f"""
        You are an expert AI Developer Advocate, Technical Writer, and Open Source Documentation Specialist.

        Your task is to transform the provided GitHub repository into a publication-ready, highly engaging, technically accurate README.

        Writing Style:
        {style}

        User Goal:
        {goal if goal else "Improve the repository for public sharing, discoverability, and technical clarity."}

        Repository README:
        {readme[:4000]}

        Relevant examples and external references:
        {example_text}

        OBJECTIVE

        Analyze the repository and generate an improved README that accurately represents the project.

        Do NOT use generic templates.

        Instead, infer the repository's purpose, architecture, workflow, users, technologies, and strengths from the provided repository information.

        Every recommendation must be grounded in available repository evidence. If information cannot be confirmed, clearly indicate uncertainty rather than inventing details.

        CONTENT REQUIREMENTS

        Your generated README should include appropriate sections based on the repository.

        Possible sections include (only include when relevant):
        - Project Title
        - Short Project Summary
        - Overview
        - Why This Project Matters
        - Problem Statement
        - Key Features
        - Repository Highlights
        - Architecture
        - System Workflow
        - Project Structure
        - Installation
        - Requirements
        - Quick Start
        - Usage Examples
        - Configuration
        - Technologies Used
        - Model(s)
        - Dataset Information
        - API Reference
        - Evaluation
        - Results
        - Benchmarks
        - Performance
        - Screenshots Placeholders
        - Examples
        - Testing
        - Deployment
        - Contributing
        - Roadmap
        - FAQ
        - License
        - Citation
        - Acknowledgements

        Choose sections dynamically.

        Never include irrelevant sections.

        ESSENTIAL README ELEMENTS

        Whenever relevant, include the following repository-specific details:
        - a clear project name and one-line value proposition
        - the problem the project solves
        - the core solution or approach
        - how the system works or is used
        - prerequisites and installation steps
        - quick-start examples
        - architecture or workflow explanation
        - key technical components and dependencies
        - evaluation, benchmarks, or results when available
        - limitations, assumptions, or known issues
        - contribution and support guidance
        - license, citation, or acknowledgements when appropriate

        For AI/ML repositories, also include relevant details about models, datasets, training strategy, evaluation metrics, and reproducibility when supported by the repository evidence.

        REPOSITORY ANALYSIS

        Before writing, analyze:
        - repository purpose
        - target users
        - major features
        - technologies
        - architecture
        - workflow
        - installation process
        - strengths
        - weaknesses
        - missing documentation
        - missing developer information
        - discoverability
        - readability

        Use these findings throughout the README.

        DOCUMENTATION IMPROVEMENTS

        Improve:
        - clarity
        - organization
        - readability
        - navigation
        - consistency
        - completeness
        - developer experience

        Rewrite weak sections.

        Expand incomplete sections.

        Keep strong existing content.

        DISCOVERABILITY

        Improve discoverability by naturally optimizing:
        - repository title
        - summary
        - headings
        - keywords
        - terminology
        - GitHub search relevance

        Do NOT create a keyword list.

        Instead integrate keywords naturally.

        TECHNICAL ACCURACY

        Never invent:
        - features
        - benchmarks
        - datasets
        - APIs
        - models
        - integrations
        - metrics
        - architecture

        If something appears incomplete or uncertain:
        - explicitly state that additional repository information would be needed.

        VISUAL PRESENTATION

        Produce a visually engaging README.

        Use:
        - emojis for headings
        - markdown tables
        - checklists
        - blockquotes
        - collapsible sections where useful
        - code blocks
        - callouts
        - horizontal rules

        When appropriate, generate Mermaid diagrams for:
        - architecture
        - workflow
        - pipeline
        - component interaction

        Only generate diagrams when enough information exists.

        EXAMPLES

        If enough information exists, generate:
        - installation example
        - usage example
        - CLI example
        - API example
        - expected output example

        Otherwise omit them.

        AUDIENCE ADAPTATION

        Infer the primary audience.

        Examples include:
        - AI researchers
        - ML engineers
        - developers
        - students
        - contributors
        - end users

        Adjust tone and explanations accordingly.

        README QUALITY

        Ensure the README is:
        - technically accurate
        - easy to scan
        - beginner friendly
        - professional
        - publication ready
        - visually engaging
        - repository specific

        OUTPUT RULES

        Output ONLY the improved README in Markdown.

        Do NOT explain your reasoning.

        Do NOT mention these instructions.

        Do NOT use placeholder text unless repository information is genuinely unavailable.

        Do NOT produce a generic README template.

        Generate documentation that feels uniquely written for this repository and fully aligned with the user's stated goal.
        ADDITIONAL REQUIREMENTS

        - Rewrite the README specifically for this repository, not as a generic template.
        - Extract the actual project purpose, main workflow, and standout capabilities from the supplied README and repository context.
        - Highlight project-specific details such as the problem solved, target users, core features, architecture, and expected outcomes.
        - Recommend a better project title or summary only if it improves clarity for the repository.
        - Suggest relevant tags or categories,
        - Identify missing sections or unclear parts of the README and add them in a polished way.
        - Propose visual or structural enhancements such as diagrams, tables, callouts, code blocks, and step-by-step examples.
        - Make the README more discoverable, clear, complete, and publication-ready.
        - Tailor the content to the most likely audience: developers, researchers, contributors, or end users.
        - If the repository is an AI/ML or agentic project, emphasize architecture, tooling, workflows, and practical value clearly.
        - Avoid inventing features; if something is uncertain, describe it cautiously and accurately.

        STRICT CONSTRAINTS

        1. Use relevant emojis for EVERY header and for key feature points.
        2. Use bullet points, checklists, and callouts extensively. Avoid long paragraphs (no "passages").
        3. Include clear, attractive sections like:
            - 🌍 Introduction
            - 🎯 **Value Proposition** (Address the user's specific goal if provided)
            - 🚀 **Quick Start**
            - 🛠️ **Tech Stack** (Use a bulleted list with emojis)
            - 📝 **Architecture & Structure** (Deep dive into the project's logic)
            - 🌟 **Key Features**
            - 👥 **Who Should Use This**
            - ✅ **Success Criteria**
        4. Make the tone professional but high-energy and visually engaging.
        5. Use Markdown tables where appropriate for technical specs or comparisons.
        6. Use interactive elements where possible (e.g., checklists, collapsible sections, callouts, or code blocks for demos).
        7. DO NOT output a passage or essay. Output must be a visually engaging, sectioned, and interactive-ready article.
        8. If the user specified a goal, make sure that goal is prominently addressed in the text.
        9. Output ONLY the improved README markdown, using Markdown and HTML for visual effects.



        """

        try:
            # Use the correct client and model based on provider
            client = self.active_client
            model = self.selected_model
            if client is None:
                logger.warning(
                    "No LLM client available in summarize_and_improve; returning simple heuristic improvement.")
                lines = readme.splitlines()
                title = lines[0] if lines else "Project"
                return f"# {title}\n\nImproved summary: This project implements X. Add Installation and Usage sections."

            # Google Gemini
            if self.provider == "google" and hasattr(client, "models"):
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                    if not response or not response.text:
                        logger.error("Gemini returned empty response")
                        return "Error: AI generated an empty response."
                    return response.text
                except Exception as e:
                    logger.error(
                        f"Gemini call failed, trying Groq if available: {e}")
                    # Fallback to Groq if available
                    if self.groq_client:
                        try:
                            # Always use a valid Groq model for fallback
                            groq_model = "llama-3.1-8b-instant"
                            groq_response = self.groq_client.chat.completions.create(
                                model=groq_model,
                                messages=[{"role": "user", "content": prompt}]
                            )
                            return groq_response.choices[0].message.content
                        except Exception as e2:
                            logger.error(f"Groq fallback also failed: {e2}")
                            return f"Error generating improvement suggestions: {str(e2)}"
                    return f"Error generating improvement suggestions: {str(e)}"

            # Groq (Llama)
            if self.provider == "groq" and hasattr(client, "chat"):
                try:
                    groq_response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return groq_response.choices[0].message.content
                except Exception as e:
                    logger.error(
                        f"Groq call failed, trying Gemini if available: {e}")
                    # Fallback to Gemini if available
                    if self.gemini_client:
                        try:
                            # Always use a valid Gemini model for fallback
                            gemini_model = "gemini-1.5-flash-latest"
                            response = self.gemini_client.models.generate_content(
                                model=gemini_model,
                                contents=prompt
                            )
                            if not response or not response.text:
                                logger.error("Gemini returned empty response")
                                return "Error: AI generated an empty response."
                            return response.text
                        except Exception as e2:
                            logger.error(f"Gemini fallback also failed: {e2}")
                            return f"Error generating improvement suggestions: {str(e2)}"
                    return f"Error generating improvement suggestions: {str(e)}"

            # If all else fails
            logger.error("No valid LLM provider or client found.")
            return "Error: No valid LLM provider or client found."
        except Exception as e:
            logger.exception(f"LLM generation crash: {e}")
            return f"Error generating improvement suggestions: {str(e)}"
