
import os
import logging
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[Warning] python-dotenv not installed. .env file will not be loaded automatically.")
try:
    from google import genai
except ImportError:
    genai = None
try:
    from groq import Groq
except ImportError:
    Groq = None


def list_gemini_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not genai or not api_key:
        print("[Gemini] google-genai not installed or GOOGLE_API_KEY missing.")
        return
    try:
        client = genai.Client(api_key=api_key)
        models = client.models.list()
        print("[Gemini] Available models:")
        for m in models:
            print(f"  - {getattr(m, 'name', getattr(m, 'id', str(m)))}")
    except Exception as e:
        print(f"[Gemini] Error listing models: {e}")


def list_groq_models():
    api_key = os.getenv("GROQ_API_KEY")
    if not Groq or not api_key:
        print("[Groq] groq not installed or GROQ_API_KEY missing.")
        return
    try:
        client = Groq(api_key=api_key)
        models = client.models.list()
        print("[Groq] Available models:")
        for m in models:
            print(f"  - {getattr(m, 'id', str(m))}")
    except Exception as e:
        print(f"[Groq] Error listing models: {e}")


if __name__ == "__main__":
    print("Listing available models for Gemini and Groq...")
    list_gemini_models()
    list_groq_models()
