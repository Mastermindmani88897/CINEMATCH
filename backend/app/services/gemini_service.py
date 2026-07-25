"""
CineMatch AI — Google Gemini AI Integration Service
Generates AI recommendation explanations, movie summaries, semantic search augmentations, and AI assistant responses.
Falls back gracefully with a friendly message if GEMINI_API_KEY is missing or Gemini API is unavailable.

UPDATED: Uses google-genai SDK (replaces deprecated google-generativeai).
"""

import logging
import asyncio
from typing import Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)

_gemini_client = None
_gemini_model_name = None
UNAVAILABLE_MESSAGE = "Gemini AI service is currently unavailable. Please verify your GEMINI_API_KEY or try again later."


def get_gemini_model():
    """Initialize and return a cached Gemini generative model."""
    global _gemini_client, _gemini_model_name
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "":
        return None
    if _gemini_client is not None:
        return _gemini_client

    try:
        import warnings
        warnings.filterwarnings("ignore", category=FutureWarning)

        # Try new google-genai SDK first
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            # Store client for async usage
            _gemini_client = client
            _gemini_model_name = "gemini-2.0-flash"
            logger.info(f"Google Gemini AI (google-genai SDK) initialized with model '{_gemini_model_name}'.")
            return _gemini_client
        except ImportError:
            pass

        # Fallback: try legacy google.generativeai
        try:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=settings.GEMINI_API_KEY)
            # Updated model candidates — older SDK used different model names
            candidates = [
                "gemini-2.0-flash-exp",
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-1.5-flash-latest",
                "gemini-1.5-pro",
                "gemini-pro",
            ]
            for model_name in candidates:
                try:
                    m = genai_legacy.GenerativeModel(model_name)
                    _gemini_client = m
                    _gemini_model_name = model_name
                    logger.info(f"Google Gemini AI (legacy SDK) initialized with model '{model_name}'.")
                    return _gemini_client
                except Exception as ex:
                    logger.debug(f"Model candidate '{model_name}' failed: {ex}")
                    continue
        except ImportError:
            pass

    except Exception as e:
        logger.warning(f"Failed to initialize Google Gemini AI client: {e}")
    return None


async def _generate_text(prompt: str) -> Optional[str]:
    """Generate text using the Gemini model. Handles both google-genai and legacy SDKs."""
    model = get_gemini_model()
    if model is None:
        return None

    try:
        # New google-genai SDK
        from google import genai
        if isinstance(model, genai.Client):
            response = await asyncio.to_thread(
                model.models.generate_content,
                model=_gemini_model_name,
                contents=prompt,
            )
            return response.text.strip() if response and response.text else None

        # Legacy SDK — use asyncio.to_thread to avoid blocking the event loop
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text.strip() if response and response.text else None

    except Exception as e:
        logger.warning(f"Gemini text generation error: {e}")
        return None


async def generate_explanation(source_movie: dict, recommended_movie: dict) -> str:
    """Generate human-readable AI explanation for why a movie is recommended."""
    source_title = source_movie.get("title", "your favorite movie")
    rec_title = recommended_movie.get("title", "this movie")
    genres = ", ".join(recommended_movie.get("genres") or [])
    director = recommended_movie.get("director", "")

    prompt = (
        f"Explain in 2 concise, engaging sentences why a film enthusiast who enjoyed '{source_title}' "
        f"would also love watching '{rec_title}'. Mention relevant genres ({genres}) or director style ({director})."
    )

    result = await _generate_text(prompt)
    if result:
        return result

    # Friendly fallback
    genres_short = ", ".join((recommended_movie.get("genres") or [])[:2])
    return (
        f"This movie is recommended because it shares {genres_short or 'similar'} thematic elements "
        f"and cinematic style with {source_title}."
    )


async def generate_movie_summary(title: str, overview: str) -> str:
    """Generate a punchy 1-sentence AI summary for a movie."""
    if overview:
        prompt = f"Summarize the plot of the movie '{title}' in one punchy, exciting sentence based on: {overview}"
        result = await _generate_text(prompt)
        if result:
            return result

    if overview:
        return overview[:150] + ("..." if len(overview) > 150 else "")
    return f"A compelling story titled {title}."


async def semantic_search_query_expansion(query: str) -> List[str]:
    """Expand user's freeform search query into semantic keywords using Gemini AI."""
    prompt = (
        f"Extract 5 core search keywords or genre themes from this natural language movie request: '{query}'. "
        f"Return ONLY a comma-separated list of words."
    )
    result = await _generate_text(prompt)
    if result:
        keywords = [k.strip() for k in result.split(",") if k.strip()]
        if keywords:
            return keywords

    return [q for q in query.split() if len(q) > 2]


async def ai_assistant_search(query: str) -> str:
    """AI Conversational Movie Assistant providing recommendations based on freeform user query."""
    prompt = (
        f"You are CineMatch AI, an expert movie concierge. The user asks: '{query}'. "
        f"Provide a friendly response recommending 3 specific movies with brief 1-sentence reasons why each fits their mood."
    )
    result = await _generate_text(prompt)
    if result:
        return result

    return (
        f"Here are matches for '{query}'. "
        f"Note: {UNAVAILABLE_MESSAGE}"
    )


async def compare_movies(movie_a: dict, movie_b: dict) -> str:
    """Compare two movies across themes, pacing, tone, and audience appeal."""
    title_a = movie_a.get("title", "Movie A")
    title_b = movie_b.get("title", "Movie B")
    prompt = (
        f"Provide a captivating 3-bullet comparison between '{title_a}' and '{title_b}' "
        f"comparing their narrative themes, tone/pacing, and who would enjoy which one more."
    )
    result = await _generate_text(prompt)
    if result:
        return result

    return f"Comparative analysis between '{title_a}' and '{title_b}': Both films offer unique narrative experiences in their respective genres."


async def explain_ending(title: str, overview: str, include_spoilers: bool = False) -> str:
    """Explain the ending of a movie with optional spoiler warnings."""
    spoiler_flag = "INCLUDE SPOILERS" if include_spoilers else "DO NOT include major plot spoilers"
    prompt = (
        f"Explain the ending and key thematic climax of the film '{title}' ({overview[:200]}). "
        f"Constraint: {spoiler_flag}. Keep it to 3 insightful sentences."
    )
    result = await _generate_text(prompt)
    if result:
        return result

    return f"The climax of '{title}' resolves the central thematic conflict, leaving viewers with lingering philosophical questions."
