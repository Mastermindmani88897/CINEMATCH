"""
CineMatch AI — AI Explanation Generator
Generates human-readable explanations for why a movie was recommended.
"""

import random
from typing import List, Dict, Optional
import pandas as pd


EXPLANATION_TEMPLATES = [
    "Recommended because it shares {shared_features} with {source_title}.",
    "You might love this — it features {shared_features}, just like {source_title}.",
    "A great pick if you enjoyed {source_title}: both explore {shared_features}.",
    "This movie matches your taste for {shared_features} found in {source_title}.",
    "Strong similarities in {shared_features} make this a top pick based on {source_title}.",
]

MOOD_TEMPLATES = [
    "Selected for your {mood} mood — features {shared_features}.",
    "Perfect for a {mood} watch — this film delivers {shared_features}.",
]

GENRE_TEMPLATES = [
    "Top pick in {genre} — rated {rating}/10 with {vote_count}+ votes.",
    "A highly-rated {genre} film that fans consistently love.",
]

PERSONALIZED_TEMPLATES = [
    "Tailored for you based on your viewing history and favorite genres: {shared_features}.",
    "Matches your taste profile — you love {shared_features}.",
    "Based on your favorites, this film checks your key preferences: {shared_features}.",
]

MOVIE_PERSONALITY_PROFILES = [
    ("Emotional Sci-Fi Explorer", ["Science Fiction", "Drama"], "You enjoy emotionally rich science fiction and thought-provoking narratives."),
    ("Thriller Addict", ["Thriller", "Crime", "Mystery"], "You're drawn to edge-of-your-seat suspense and psychological complexity."),
    ("Romantic Dreamer", ["Romance", "Drama"], "You appreciate heartfelt stories and emotional connection."),
    ("Action Hero", ["Action", "Adventure"], "You love high-energy films with dynamic sequences and strong heroes."),
    ("Comedy Enthusiast", ["Comedy", "Animation"], "You prefer feel-good films that bring laughter and lightness."),
    ("Horror Buff", ["Horror"], "You embrace fear and the thrill of the unknown."),
    ("Fantasy Wanderer", ["Fantasy", "Adventure"], "You love epic worlds, magic, and mythological journeys."),
    ("Documentary Thinker", ["Documentary"], "You value truth, insight, and real-world stories."),
    ("Cinephile", [], "You have eclectic tastes and appreciate film as an art form."),
]


class ExplanationGenerator:
    """Generates AI-style explanations for movie recommendations."""

    def generate_content_explanation(
        self,
        source_movie: Dict,
        recommended_movie: Dict,
        similarity_score: float,
    ) -> Dict:
        """Generate explanation for content-based recommendation."""
        source_genres = set(source_movie.get("genres") or [])
        rec_genres = set(recommended_movie.get("genres") or [])
        shared_genres = list(source_genres & rec_genres)

        source_cast = set((source_movie.get("cast_names") or [])[:5])
        rec_cast = set((recommended_movie.get("cast_names") or [])[:5])
        shared_cast = list(source_cast & rec_cast)

        source_keywords = set(source_movie.get("keywords") or [])
        rec_keywords = set(recommended_movie.get("keywords") or [])
        shared_keywords = list(source_keywords & rec_keywords)[:5]

        # Build feature description
        feature_parts = []
        if shared_genres:
            feature_parts.append(f"{', '.join(shared_genres[:3])} themes")
        if shared_cast:
            feature_parts.append(f"performances by {', '.join(shared_cast[:2])}")
        if shared_keywords:
            feature_parts.append(f"elements of {', '.join(shared_keywords[:3])}")
        if source_movie.get("director") and source_movie.get("director") == recommended_movie.get("director"):
            feature_parts.append(f"the directing style of {source_movie['director']}")

        if not feature_parts:
            feature_parts = ["similar storytelling style and atmosphere"]

        shared_features = ", ".join(feature_parts)
        template = random.choice(EXPLANATION_TEMPLATES)
        explanation = template.format(
            shared_features=shared_features,
            source_title=source_movie.get("title", "your selection"),
        )

        return {
            "explanation": explanation,
            "shared_genres": shared_genres,
            "shared_keywords": shared_keywords,
            "shared_cast": shared_cast,
            "similarity_score": similarity_score,
        }

    def generate_mood_explanation(self, mood: str, movie: Dict) -> str:
        genres = ", ".join((movie.get("genres") or [])[:3])
        template = random.choice(MOOD_TEMPLATES)
        return template.format(mood=mood, shared_features=genres or "great storytelling")

    def generate_genre_explanation(self, genre: str, movie: Dict) -> str:
        template = random.choice(GENRE_TEMPLATES)
        return template.format(
            genre=genre,
            rating=round(movie.get("vote_average", 0), 1),
            vote_count=movie.get("vote_count", 0),
        )

    def generate_personalized_explanation(self, movie: Dict, user_genres: List[str]) -> str:
        movie_genres = movie.get("genres") or []
        shared = [g for g in movie_genres if g in user_genres]
        features = ", ".join(shared[:3]) if shared else "your preferred genres"
        template = random.choice(PERSONALIZED_TEMPLATES)
        return template.format(shared_features=features)

    def analyze_taste(self, genre_counts: Dict[str, int], total: int) -> Dict:
        """Generate AI taste personality from genre statistics."""
        if not genre_counts or total == 0:
            return {
                "personality": "Cinephile",
                "personality_description": "You have diverse, eclectic tastes across all genres.",
            }

        top_genres = sorted(genre_counts, key=genre_counts.get, reverse=True)[:3]

        # Match personality profile
        best_match = MOVIE_PERSONALITY_PROFILES[-1]  # default: Cinephile
        for profile_name, profile_genres, description in MOVIE_PERSONALITY_PROFILES[:-1]:
            if any(g in top_genres for g in profile_genres):
                best_match = (profile_name, profile_genres, description)
                break

        return {
            "personality": best_match[0],
            "personality_description": best_match[2],
        }
