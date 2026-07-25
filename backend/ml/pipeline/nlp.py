"""
CineMatch AI — NLP Pipeline
Handles tokenization, stop word removal, lemmatization, and stemming.
"""

import re
import string
import logging
from typing import List

logger = logging.getLogger(__name__)

# Try importing NLTK components; download if missing
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer, WordNetLemmatizer
    from nltk.tokenize import word_tokenize

    def _ensure_nltk():
        resources = ["punkt", "stopwords", "wordnet", "omw-1.4", "punkt_tab"]
        for r in resources:
            try:
                nltk.data.find(f"tokenizers/{r}" if r.startswith("punkt") else f"corpora/{r}")
            except LookupError:
                logger.info(f"Downloading NLTK resource: {r}")
                nltk.download(r, quiet=True)

    _ensure_nltk()
    STOP_WORDS = set(stopwords.words("english"))
    stemmer = PorterStemmer()
    lemmatizer = WordNetLemmatizer()
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    STOP_WORDS = set()
    stemmer = None
    lemmatizer = None
    logger.warning("NLTK not available — using basic text cleaning only")

CUSTOM_STOP_WORDS = {
    "film", "movie", "story", "one", "two", "three", "man", "woman",
    "world", "life", "time", "day", "year", "new", "must", "find",
    "take", "back", "get", "make", "way", "use", "go", "come",
}
ALL_STOP_WORDS = STOP_WORDS | CUSTOM_STOP_WORDS


def tokenize(text: str) -> List[str]:
    """Tokenize text into words."""
    if not text:
        return []
    if NLTK_AVAILABLE:
        try:
            return word_tokenize(text.lower())
        except Exception:
            pass
    return re.findall(r"\b[a-z]+\b", text.lower())


def remove_punctuation(text: str) -> str:
    """Remove punctuation from text."""
    return text.translate(str.maketrans("", "", string.punctuation))


def remove_stopwords(tokens: List[str]) -> List[str]:
    """Remove stop words from token list."""
    return [t for t in tokens if t not in ALL_STOP_WORDS and len(t) > 2]


def lemmatize(tokens: List[str]) -> List[str]:
    """Apply lemmatization to tokens."""
    if not NLTK_AVAILABLE or lemmatizer is None:
        return tokens
    return [lemmatizer.lemmatize(t) for t in tokens]


def stem(tokens: List[str]) -> List[str]:
    """Apply stemming to tokens."""
    if not NLTK_AVAILABLE or stemmer is None:
        return tokens
    return [stemmer.stem(t) for t in tokens]


def full_nlp_pipeline(text: str, apply_stemming: bool = False) -> str:
    """
    Full NLP pipeline:
    lowercase → remove punctuation → tokenize → remove stopwords → lemmatize → (optional stem)
    """
    if not text or not isinstance(text, str):
        return ""
    
    text = text.lower()
    text = remove_punctuation(text)
    tokens = tokenize(text)
    tokens = [t for t in tokens if t.isalpha()]  # keep only alphabetic tokens
    tokens = remove_stopwords(tokens)
    tokens = lemmatize(tokens)
    
    if apply_stemming:
        tokens = stem(tokens)
    
    return " ".join(tokens)


def process_feature_for_tfidf(text: str) -> str:
    """
    Lighter NLP for TF-IDF: skip stemming to preserve semantic meaning.
    """
    return full_nlp_pipeline(text, apply_stemming=False)


def process_query(query: str) -> str:
    """Process user search query through NLP pipeline."""
    return full_nlp_pipeline(query, apply_stemming=False)
