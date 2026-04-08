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
        You are an expert developer advocate and technical writer. 
        Your task is to transform a GitHub repository README into a beautiful, highly engaging, and interactive-style project showcase.

        Writing Style: {style}
        User's Specific Focus/Goal: {goal if goal else "General repository improvement"}

        Current README content:
        {readme[:4000]}

        Relevant search results for similar successful projects:
        {example_text}

        PROJECT REQUIREMENTS:
        - Recommend a better project title or summary (but do NOT output a title at the top; just improve the content)
        - Suggest relevant tags or categories (but do NOT output tags or badges; just improve the content)
        - Identify missing sections or unclear parts of the README and add them
        - Propose visual or structural enhancements (e.g., diagrams, layout, code blocks, tables)
        - Make the README more discoverable, clear, and complete
        - Collaborate as if you are part of a multi-agent system (Repo Analyzer, Metadata Recommender, Content Improver, Reviewer/Critic, Fact-Checker)
        - Use tool-augmented reasoning (web search, RAG, keyword extraction, etc.)

        STRICT CONSTRAINTS:
        1. Use relevant emojis for EVERY header and for key feature points.
        2. Use bullet points, checklists, and callouts extensively. Avoid long paragraphs (no "passages").
        3. Include clear, attractive sections like:
            - 🌍 Introduction
            - 🎯 **Value Proposition** (Address the user's specific goal if provided)
            - 🚀 **Quick Start** (How to get up and running in 3 steps)
            - 🛠️ **Tech Stack** (Use a bulleted list with emojis)
            - 📝 **Architecture & Structure** (Deep dive into the project's logic)
            - 🌟 **Key Features**
            - 👥 **Who Should Use This** 
            - ✅ **Success Criteria**
        4. Make the tone professional but high-energy and visually engaging.
        5. Use Markdown tables where appropriate for technical specs or comparisons.
        6. Use interactive elements where possible (e.g., checklists, collapsible sections, callouts, or code blocks for demos).
        7. DO NOT output a passage or essay. Output must be a visually engaging, sectioned, and interactive-ready article.
        8. If the user specified a goal (e.g., "{goal}"), make sure that goal is prominently addressed in the text.

        Output ONLY the improved README markdown, using Markdown and HTML for visual effects. DO NOT include any tags, badges, or tag sections at the top. DO NOT output any tag or badge HTML or markdown.
        


## 🌍 Introduction

> **Publication Assistant for AI Projects** is a **tool-augmented, multi-agent system** that **systematically upgrades how AI/ML repositories are presented for public sharing**.  
> It performs **deep repository analysis**—covering **README, structure, code signals, and metadata**—and returns **actionable, evidence-backed recommendations** to improve:

- 🔎 **Discoverability** (keywords, summaries, structure)
- 📖 **Clarity & readability** (sections, flow, examples)
- 🧩 **Structural completeness** (missing or weak areas)
- 🧠 **Technical credibility** (fact-checked claims)

✔️ Built for **AI developers, researchers, open-source maintainers, and agentic-system builders**  
✔️ Designed as a **real-world reference implementation** of **multi-agent orchestration + tool integration**



## 🎯 Value Proposition

- ✅ Transform **weak or incomplete READMEs** into **publication-ready documentation**
- ✅ Boost **GitHub visibility** without manual SEO work
- ✅ Replace **single-LLM writing** with **collaborative agent reasoning**
- ✅ Showcase **production-grade agentic architecture**
- ✅ Serve as a **learning & evaluation benchmark** for multi-agent systems


## 🧠 What This System Does (at a Glance)

- 🗂️ **Analyzes** repository structure, README, and signals
- 🏷️ **Recommends** better summaries, keywords, and categories
- ✍️ **Improves** clarity, layout, and section organization
- 🧐 **Reviews** for gaps, ambiguity, and redundancy
- ✅ **Validates** claims using tools (web search, retrieval)

---

## 🚫 What This System Does NOT Do

- ❌ Does not auto-publish changes to your repo
- ❌ Does not fabricate features or results
- ❌ Does not replace human judgment (human-in-the-loop supported)



## 🚀 Quick Start (3 Steps)

1️⃣ **Provide a GitHub Repository URL**  
2️⃣ **(Optional) Add a short project goal or focus**  
3️⃣ **Receive structured, actionable improvement suggestions**

```text
Input  → GitHub Repo (+ optional context)
Agents → Analyze • Improve • Validate • Recommend
Output → Enhanced README + Structural Guidance

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
