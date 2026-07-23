"""
CineMatch AI — ML Training Script
Run this to train all models and save them to ml/models/
Usage: python -m ml.train
"""

import logging
import sys
import argparse
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.pipeline.preprocess import load_and_merge_datasets, preprocess, save_processed_data
from ml.pipeline.tfidf_engine import TFIDFEngine
from ml.pipeline.recommendation_engines import PopularityEngine

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def train_tfidf(df):
    logger.info("=== Training TF-IDF Engine ===")
    engine = TFIDFEngine()
    engine.train(df)
    engine.save()
    logger.info("TF-IDF engine saved [OK]")
    return engine


def train_popularity(df):
    logger.info("=== Training Popularity Engine ===")
    engine = PopularityEngine()
    engine.fit(df)
    engine.save()
    logger.info("Popularity engine saved [OK]")
    return engine


def train_semantic(df, skip=False):
    if skip:
        logger.warning("Skipping semantic engine (--skip-semantic flag set)")
        return None
    logger.info("=== Training Semantic Engine ===")
    from ml.pipeline.semantic_engine import SemanticEngine
    engine = SemanticEngine()
    engine.train(df)
    engine.save()
    logger.info("Semantic engine saved [OK]")
    return engine


def main():
    parser = argparse.ArgumentParser(description="Train CineMatch AI ML models")
    parser.add_argument("--skip-semantic", action="store_true", help="Skip Sentence Transformer training")
    args = parser.parse_args()

    logger.info("==========================================")
    logger.info("   CineMatch AI - Model Training Script   ")
    logger.info("==========================================")

    logger.info("Step 1/4: Loading and preprocessing dataset...")
    df = load_and_merge_datasets()
    df = preprocess(df)
    save_processed_data(df)
    logger.info(f"Dataset ready: {len(df)} movies")

    logger.info("Step 2/4: Training TF-IDF content engine...")
    train_tfidf(df)

    logger.info("Step 3/4: Training popularity engine...")
    train_popularity(df)

    logger.info("Step 4/4: Training semantic search engine...")
    train_semantic(df, skip=args.skip_semantic)

    logger.info("==========================================")
    logger.info("   [OK] All models trained and saved!     ")
    logger.info(f"   Models directory: {MODELS_DIR}        ")
    logger.info("==========================================")


if __name__ == "__main__":
    main()
