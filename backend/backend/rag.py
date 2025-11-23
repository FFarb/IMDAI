"""RAG (Retrieval-Augmented Generation) module for style retrieval using ChromaDB."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)

# ChromaDB storage path
CHROMA_DB_PATH = Path(__file__).parent.parent / ".chromadb"
COLLECTION_NAME = "style_presets"


def init_vector_store() -> chromadb.Collection:
    """Initialize ChromaDB vector store with OpenAI embeddings.
    
    Returns:
        ChromaDB collection for storing and retrieving style presets.
    """
    # Create ChromaDB client with persistent storage
    client = chromadb.PersistentClient(
        path=str(CHROMA_DB_PATH),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        ),
    )
    
    # Get or create collection
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
        logger.info(f"Loaded existing collection '{COLLECTION_NAME}' with {collection.count()} items")
    except Exception:
        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Image generation style presets"},
        )
        logger.info(f"Created new collection '{COLLECTION_NAME}'")
    
    return collection


def seed_presets(presets_path: str | Path) -> int:
    """Seed the vector store with presets from a JSON file.
    
    Args:
        presets_path: Path to the presets.json file.
        
    Returns:
        Number of presets added to the vector store.
    """
    presets_path = Path(presets_path)
    if not presets_path.exists():
        logger.error(f"Presets file not found: {presets_path}")
        return 0
    
    # Load presets
    with open(presets_path, "r", encoding="utf-8") as f:
        presets = json.load(f)
    
    if not presets:
        logger.warning("No presets found in file")
        return 0
    
    # Initialize vector store
    collection = init_vector_store()
    
    # Initialize OpenAI embeddings
    embeddings_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    # Prepare documents for embedding
    documents = []
    metadatas = []
    ids = []
    
    for idx, (preset_name, preset_data) in enumerate(presets.items()):
        # Create a rich text representation for embedding
        doc_text = f"""
Style: {preset_name}
Subject: {preset_data.get('subject', '')}
Style: {preset_data.get('style', '')}
Composition: {preset_data.get('composition', '')}
Lighting: {preset_data.get('lighting', '')}
Mood: {preset_data.get('mood', '')}
Details: {preset_data.get('details', '')}
Quality: {preset_data.get('quality', '')}
        """.strip()
        
        documents.append(doc_text)
        metadatas.append({
            "name": preset_name,
            **preset_data,
        })
        ids.append(f"preset_{idx}")
    
    # Generate embeddings
    logger.info(f"Generating embeddings for {len(documents)} presets...")
    embeddings = embeddings_model.embed_documents(documents)
    
    # Add to ChromaDB
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )
    
    logger.info(f"Successfully seeded {len(documents)} presets to vector store")
    return len(documents)



def index_strategy(strategy_id: str, strategy_name: str, strategy_data: dict[str, Any]) -> str:
    """Index a single strategy into ChromaDB.
    
    Args:
        strategy_id: Unique ID for the strategy.
        strategy_name: Name of the strategy.
        strategy_data: Dictionary containing strategy details.
        
    Returns:
        The document ID used in ChromaDB.
    """
    collection = init_vector_store()
    
    # Initialize OpenAI embeddings
    embeddings_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    # Create a rich text representation for embedding
    doc_text = f"""
Strategy: {strategy_name}
Subject: {strategy_data.get('core_subject', '')}
Style: {strategy_data.get('visual_style', '')}
Composition: {strategy_data.get('composition', '')}
Mood: {strategy_data.get('mood', '')}
Constraints: {strategy_data.get('technical_constraints', '')}
Commercial Hook: {strategy_data.get('commercial_hook', '')}
    """.strip()
    
    # Generate embedding
    embedding = embeddings_model.embed_query(doc_text)
    
    # Add to ChromaDB
    doc_id = f"strategy_{strategy_id}"
    collection.upsert(
        documents=[doc_text],
        embeddings=[embedding],
        metadatas=[{
            "name": strategy_name,
            "type": "user_strategy",
            "is_favorite": True,
            **{k: str(v) for k, v in strategy_data.items() if isinstance(v, (str, int, float, bool))}
        }],
        ids=[doc_id],
    )
    
    return doc_id


def retrieve_similar_styles(query: str, k: int = 3, filter_favorites: bool = False) -> list[dict[str, Any]]:
    """Retrieve similar style presets based on a query.
    
    Args:
        query: Search query (user brief + vision analysis).
        k: Number of similar styles to retrieve.
        filter_favorites: If True, only retrieve items marked as favorites.
        
    Returns:
        List of similar style presets with metadata.
    """
    collection = init_vector_store()
    
    if collection.count() == 0:
        logger.warning("Vector store is empty. Run seed_presets() first.")
        return []
    
    # Initialize embeddings model
    embeddings_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    # Generate query embedding
    query_embedding = embeddings_model.embed_query(query)
    
    # Prepare filter
    where_filter = {"is_favorite": True} if filter_favorites else None
    
    # Search for similar styles
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k, collection.count()),
        where=where_filter
    )
    
    # Format results
    similar_styles = []
    if results and results["metadatas"] and results["metadatas"][0]:
        for metadata, distance in zip(results["metadatas"][0], results["distances"][0]):
            similar_styles.append({
                "name": metadata.get("name", "Unknown"),
                "subject": metadata.get("core_subject", metadata.get("subject", "")),
                "style": metadata.get("visual_style", metadata.get("style", "")),
                "composition": metadata.get("composition", ""),
                "lighting": metadata.get("lighting", ""),
                "mood": metadata.get("mood", ""),
                "details": metadata.get("details", ""),
                "quality": metadata.get("quality", ""),
                "similarity_score": 1 - distance,  # Convert distance to similarity
                "raw_metadata": metadata
            })
    
    logger.info(f"Retrieved {len(similar_styles)} similar styles for query: {query[:50]}... (Filter: {filter_favorites})")
    return similar_styles


__all__ = ["init_vector_store", "seed_presets", "retrieve_similar_styles", "index_strategy"]
