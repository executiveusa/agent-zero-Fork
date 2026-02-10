"""
Compatibility shim for langchain classes removed in v1.2.9 / langchain-community v0.4.1.
Provides LocalFileStore and CacheBackedEmbeddings implementations.
"""

import hashlib
import os
from pathlib import Path
from typing import Iterator, List, Optional, Sequence, Union

from langchain_core.embeddings import Embeddings
from langchain_core.stores import ByteStore


class LocalFileStore(ByteStore):
    """Simple file-backed byte store (replacement for removed langchain class)."""

    def __init__(self, root_path: Union[str, Path]) -> None:
        self.root_path = Path(root_path)
        self.root_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        # Sanitize key to be safe as a filename
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.root_path / safe_key

    def mget(self, keys: Sequence[str]) -> List[Optional[bytes]]:
        result: List[Optional[bytes]] = []
        for key in keys:
            fp = self._get_file_path(key)
            if fp.exists():
                result.append(fp.read_bytes())
            else:
                result.append(None)
        return result

    def mset(self, key_value_pairs: Sequence[tuple[str, bytes]]) -> None:
        for key, value in key_value_pairs:
            fp = self._get_file_path(key)
            fp.write_bytes(value)

    def mdelete(self, keys: Sequence[str]) -> None:
        for key in keys:
            fp = self._get_file_path(key)
            if fp.exists():
                fp.unlink()

    def yield_keys(self, *, prefix: Optional[str] = None) -> Iterator[str]:
        for f in self.root_path.iterdir():
            if f.is_file():
                key = f.name
                if prefix is None or key.startswith(prefix):
                    yield key


class CacheBackedEmbeddings(Embeddings):
    """Embeddings wrapper that caches results in a ByteStore
    (replacement for removed langchain class)."""

    def __init__(
        self,
        underlying_embeddings: Embeddings,
        document_embedding_store: ByteStore,
        *,
        namespace: str = "",
    ) -> None:
        self.underlying_embeddings = underlying_embeddings
        self.document_embedding_store = document_embedding_store
        self.namespace = namespace

    @classmethod
    def from_bytes_store(
        cls,
        underlying_embeddings: Embeddings,
        document_embedding_store: ByteStore,
        *,
        namespace: str = "",
    ) -> "CacheBackedEmbeddings":
        return cls(
            underlying_embeddings,
            document_embedding_store,
            namespace=namespace,
        )

    def _cache_key(self, text: str) -> str:
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{self.namespace}_{h}" if self.namespace else h

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        import json as _json

        keys = [self._cache_key(t) for t in texts]
        cached = self.document_embedding_store.mget(keys)

        # Separate cached from uncached
        results: List[Optional[List[float]]] = [None] * len(texts)
        texts_to_embed: List[str] = []
        indices_to_embed: List[int] = []

        for i, (cached_val, text) in enumerate(zip(cached, texts)):
            if cached_val is not None:
                results[i] = _json.loads(cached_val.decode("utf-8"))
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(i)

        # Embed uncached texts
        if texts_to_embed:
            new_embeddings = self.underlying_embeddings.embed_documents(texts_to_embed)
            pairs = []
            for idx, emb in zip(indices_to_embed, new_embeddings):
                results[idx] = emb
                pairs.append(
                    (keys[idx], _json.dumps(emb).encode("utf-8"))
                )
            self.document_embedding_store.mset(pairs)

        return results  # type: ignore

    def embed_query(self, text: str) -> List[float]:
        return self.underlying_embeddings.embed_query(text)

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        return self.embed_query(text)
