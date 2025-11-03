import logging
from typing import List, Optional, Dict

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


logger = logging.getLogger(__name__)


class RetrieveFAISS:

    def __init__(
        self,
        persist_directory: str = "data/FAISS/vector_db",
        top_k: int = 7,
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        self.top_k = int(top_k)

        try:
            embedding_function = OpenAIEmbeddings(model=embedding_model)
            vectordb = FAISS.load_local(
                persist_directory, embedding_function, allow_dangerous_deserialization=True
            )
            # Use a plain similarity search retriever (no reranking)
            self.retriever = vectordb.as_retriever(
                search_type="similarity",
                search_kwargs={"k": self.top_k},
            )
        except Exception as e:
            logger.exception("Error inicializando RetrieveFAISS: %s", e)
            raise

    def ask(self, query: str, k: Optional[int] = None) -> List[Dict]:

        """returns list of documents for a query

        Each dict contains: {"id", "title", "content", "metadata"}.
        """

        if not query:
            return []

        # Accept override parameters from the caller
        def _safe_int(x, default):
            try:
                return int(x) if x is not None else default
            except Exception:
                return default

        k = _safe_int(k, self.top_k)

        try:
            docs = self.retriever.get_relevant_documents(query) or []
            if not docs:
                return []

            k = int(k) if k is not None else self.top_k
            docs = docs[:k]

            results: List[Dict] = []
            for i, d in enumerate(docs, start=1):
                meta = getattr(d, "metadata", {}) or {}
                doc_id = meta.get("id") or meta.get("source") or f"doc_{i}"
                title = meta.get("title") or meta.get("header") or doc_id
                content = getattr(d, "page_content", str(d))
                results.append({
                    "id": doc_id,
                    "title": title,
                    "content": content,
                    "metadata": meta,
                })

            return results
        except Exception as e:
            logger.exception("Error ejecutando búsqueda FAISS: %s", e)
            return []

    def _format_docs(self, docs: List) -> str:

        parts: List[str] = []
        for i, d in enumerate(docs, start=1):
            meta = getattr(d, "metadata", {}) or {}
            source = meta.get("source") or meta.get("id") or ""
            header = f"Documento {i}"
            if source:
                header += f" (source: {source})"
            content = getattr(d, "page_content", str(d))
            parts.append(f"{header}\n{content}\n---")
        return "\n".join(parts)
