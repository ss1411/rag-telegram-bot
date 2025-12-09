import os
import glob
import sqlite3
from typing import List, Tuple

from sentence_transformers import SentenceTransformer
from sqlite_vec import serialize_float32, load as load_vec
import requests

from config import DATA_DIR, SQLITE_DB_PATH, TOP_K, LLM_BACKEND, OPENAI_API_KEY, OPENAI_MODEL


class MiniRAG:
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(SQLITE_DB_PATH)
        self.conn.enable_load_extension(True)
        load_vec(self.conn)
        self._init_tables()
        self._maybe_ingest()

    def _init_tables(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_name TEXT,
                chunk TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS doc_vecs USING vec0(
                embedding float[384]  -- all-MiniLM-L6-v2 dim.
            )
            """
        )
        self.conn.commit()

    def _load_files(self) -> List[Tuple[str, str]]:
        paths = glob.glob(os.path.join(DATA_DIR, "*.md")) + glob.glob(
            os.path.join(DATA_DIR, "*.txt")
        )
        docs = []
        for p in paths:
            with open(p, "r", encoding="utf-8") as f:
                docs.append((os.path.basename(p), f.read()))
        return docs

    def _chunk_text(self, text: str, max_chars: int = 600) -> List[str]:
        # very simple chunker on paragraphs
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        chunks = []
        current = ""
        for p in paragraphs:
            if len(current) + len(p) + 1 <= max_chars:
                current = (current + "\n" + p).strip()
            else:
                if current:
                    chunks.append(current)
                current = p
        if current:
            chunks.append(current)
        return chunks

    def _existing_docs_count(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM docs")
        return cur.fetchone()[0]

    def _maybe_ingest(self):
        if self._existing_docs_count() > 0:
            return  # already ingested

        docs = self._load_files()
        if not docs:
            return

        cur = self.conn.cursor()

        for doc_name, text in docs:
            chunks = self._chunk_text(text)
            embeddings = self.model.encode(chunks, convert_to_numpy=True)
            for chunk, emb in zip(chunks, embeddings):
                cur.execute(
                    "INSERT INTO docs (doc_name, chunk) VALUES (?, ?)",
                    (doc_name, chunk),
                )
                rowid = cur.lastrowid
                cur.execute(
                    "INSERT INTO doc_vecs(rowid, embedding) VALUES (?, ?)",
                    (rowid, sqlite3.Binary(serialize_float32(emb))),
                )
        self.conn.commit()

    def retrieve(self, query: str, k: int = None) -> List[Tuple[str, str]]:
        if k is None:
            k = TOP_K
        q_emb = self.model.encode([query], convert_to_numpy=True)[0]
        cur = self.conn.cursor()
        cur.execute(
            """
            WITH q AS (
                SELECT ? AS embedding
            )
            SELECT d.doc_name, d.chunk
            FROM doc_vecs v
            JOIN docs d ON d.id = v.rowid
            JOIN q
            WHERE v.embedding MATCH q.embedding
            AND k = ?
            ORDER BY distance
            """,
            (sqlite3.Binary(serialize_float32(q_emb)), k),
        )
        rows = cur.fetchall()
        return [(r[0], r[1]) for r in rows]

    def build_prompt(self, query: str, contexts: List[Tuple[str, str]]) -> str:
        context_texts = []
        for doc_name, chunk in contexts:
            context_texts.append(f"[Source: {doc_name}]\n{chunk}")
        context_block = "\n\n".join(context_texts)
        prompt = (
            "You are a helpful assistant answering from the provided documents only.\n"
            "If the answer is not in the context, say you are not sure.\n\n"
            f"Context:\n{context_block}\n\n"
            f"User question: {query}\n\n"
            "Answer in a short, clear paragraph."
        )
        return prompt

    def call_llm(self, prompt: str) -> str:
        if LLM_BACKEND == "openai":
            # simple example using OpenAI’s Chat Completions
            from openai import OpenAI

            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            response = self.openai_client.responses.create(
                model=OPENAI_MODEL,
                input=[
                    {"role": "system", "content": "You are a helpful RAG assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1
            )
            model_response = response.output[0].content[0].text
            return model_response
        else:
            return "LLM backend not configured."

    def answer(self, query: str) -> str:
        ctxs = self.retrieve(query)
        if not ctxs:
            return "No knowledge base content available yet."
        prompt = self.build_prompt(query, ctxs)
        return self.call_llm(prompt)
