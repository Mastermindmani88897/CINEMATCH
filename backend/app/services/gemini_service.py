"""
CineMatch AI — Google Gemini AI Integration Service
Generates AI recommendation explanations, short movie summaries, and AI search assistance.
Falls back gracefully to template models if GEMINI_API_KEY is not configured.
"""

import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

_gemini_client = None


def get_gemini_model():
    global _gemini_client
    if not settings.GEMINI_API_KEY:
        return None
    if _gemini_client is None:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            _gemini_client = genai.GenerativeModel("gemini-1.5-flash")
            logger.info("Google Gemini AI initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini AI: {e}")
            return None
    return _gemini_client


async def generate_explanation(source_movie: dict, recommended_movie: dict) -> str:
    """Generate human-readable AI explanation via Gemini or template fallback."""
    model = get_gemini_model()
    if model:
        try:
            prompt = (
                f"Explain in 2 concise sentences why a viewer who liked '{source_movie.get('title')}' "
                f"would enjoy '{recommended_movie.get('title')}', focusing on themes ({', '.join(recommended_movie.get('genres', []))}), "
                f"directing style ({recommended_movie.get('director')}), or narrative atmosphere."
            )
            response = model.generate_content(prompt)
            if response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini API generation error: {e}")

    # Fallback template
    genres = ", ".join((recommended_movie.get("genres") or [])[:2])
    return (
        f"This movie is recommended because it shares {genres or 'similar'} themes and "
        f"cinematic tone with {source_movie.get('title', 'your selection')}."
    )


async def generate_movie_summary(title: str, overview: str) -> str:
    """Generate a 1-sentence AI summary for a movie."""
    model = get_gemini_model()
    if model and overview:
        try:
            prompt = f"Summarize the movie '{title}' in one punchy, captivating sentence: {overview}"
            response = model.generate_content(prompt)
            if response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini summary generation error: {e}")

    return overview[:150] + "..." if len(overview) > 150 else overview


async def ai_assistant_search(query: str) -> str:
    """AI Search Assistant providing recommendations for freeform query."""
    model = get_gemini_model()
    if model:
        try:
            prompt = f"The user is searching for movies with the query: '{query}'. Provide 3 movie recommendations with short 1-sentence reasons."
            response = model.generate_content(prompt)
            if response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini search assistant error: {e}")

    return f"AI Search matches for query: '{query}'"
