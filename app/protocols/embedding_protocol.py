"""Provider-independent contract for generating embeddings."""

from typing import Protocol


class EmbeddingsAdapter(Protocol):
    """Contract for an Embeddings Adapter"""
    async def generate_embedding(self, text: str) -> list[float]:
        ...
