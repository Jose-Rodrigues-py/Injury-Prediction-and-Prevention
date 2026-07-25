"""
chunking, embedding, collection creation, ingestion, search — no LLM logic.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer
import uuid

qdrant = QdrantClient("localhost", port=6333)
model = "qwen2.5:3b"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100 

# chunking
def chunk_text(text, size = CHUNK_SIZE, overlap=CHUNK_OVERLAP): 
    chunks = []
    
    start = 0
    while start < len(text): 
        chunks.append(text[start : start + size])
        start += size - overlap

    return chunks

# embed (from text to vector)
embedder = SentenceTransformer("all-MiniLM-L6-v2")
def embed(texts): 
    return embedder.encode(texts).tolist()

# store (in vector Database)
def create_collection(collection: str):
    qdrant.delete_collection(collection)
    qdrant.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

def ingest_file(text, collection: str):
    chunks = chunk_text(str(text))
    embeddings = embed(chunks)

    points = [
        PointStruct(
            id= str(uuid.uuid4()),
            vector=embeddings[i],
            payload={
                "text": chunks[i], # the actual text there contained; it looks for the closest vector (speeds up computation), and then retrieved the actual text
                "chunk_index": i # used to understand the context more (context window expansion); we can look at the x preeciding and succeeding chunks
            }
        )
        for i in range(len(chunks))
    ]

    qdrant.upsert(collection_name=collection, points=points) # this here

def search(query, collection: str, top_k=5):
    query_vector = embed([query])[0]
    
    results = qdrant.query_points(
        collection_name=collection,
        query=query_vector,
        limit=top_k
    )
    return results.points

