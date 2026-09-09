"""Qdrant semantic memory with per-user key"""
class SemanticMemory:
    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.url = qdrant_url
        # In prod: encrypt embeddings with user key before upsert
    async def upsert(self, user_id: str, text: str, embedding: list):
        pass
    async def query(self, user_id: str, embedding: list, top_k=5):
        return []
