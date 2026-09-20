"""Question/answer memory backed by ChromaDB.

We use ChromaDB's bundled ONNX MiniLM embedder by default — no network and
no extra model download is required. Users wanting better embeddings can
install the ``embeddings`` extra and swap the collection's embedding
function (see ``QuestionMemory.use_embedding_function``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config.paths import CHROMA_DIR
from app.utils.hashing import stable_hash
from app.utils.logging import get_logger

log = get_logger(__name__)

COLLECTION = "question_memory"


class QuestionMemory:
    """Persistent question/answer memory with semantic lookup."""

    def __init__(
        self,
        *,
        persist_dir: Path | None = None,
        embedding_function: Any | None = None,
    ) -> None:
        # Imported lazily so importing this module doesn't pull in chromadb on
        # cold paths like `jobassist --help`.
        import chromadb
        from chromadb.config import Settings

        directory = persist_dir or CHROMA_DIR
        directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(directory),
            settings=Settings(anonymized_telemetry=False),
        )
        kwargs: dict[str, Any] = {"name": COLLECTION}
        if embedding_function is not None:
            kwargs["embedding_function"] = embedding_function
        self.collection = self.client.get_or_create_collection(**kwargs)

    def remember(
        self,
        question: str,
        answer: str,
        *,
        category: str | None = None,
        approved: bool = False,
    ) -> str:
        """Upsert a (question, answer) pair. Returns the stable id."""
        qid = stable_hash(question.strip().lower())
        metadata: dict[str, Any] = {
            "answer": answer,
            "category": category or "",
            "approved": bool(approved),
        }
        self.collection.upsert(
            ids=[qid],
            documents=[question],
            metadatas=[metadata],
        )
        return qid

    def lookup(self, question: str, *, k: int = 3) -> list[dict[str, Any]]:
        """Return up to ``k`` semantically similar memory entries."""
        try:
            result = self.collection.query(query_texts=[question], n_results=k)
        except Exception as exc:  # ChromaDB raises diverse types; be conservative.
            log.warning("question_memory.query_failed", error=str(exc))
            return []

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        items: list[dict[str, Any]] = []
        for i, doc in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else None
            items.append(
                {
                    "question": doc,
                    "answer": metadata.get("answer", ""),
                    "category": metadata.get("category") or None,
                    "approved": bool(metadata.get("approved", False)),
                    "distance": distance,
                }
            )
        return items

    def best_match(self, question: str, *, max_distance: float = 0.35) -> dict[str, Any] | None:
        """Return the best hit if its semantic distance is under threshold."""
        matches = self.lookup(question, k=1)
        if not matches:
            return None
        m = matches[0]
        if m["distance"] is None or m["distance"] > max_distance:
            return None
        return m

    def count(self) -> int:
        return int(self.collection.count())
