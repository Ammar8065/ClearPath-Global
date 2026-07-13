"""Build the ClearPath vector database (ChromaDB) for RAG.

Two collections are created in a persistent store at rag/chroma_db/:

  rules    — one document per seeded rule: description + section reference,
             with rule_code / jurisdiction / category / risk metadata.
  sources  — the scraped official guidance pages (rag/scraped/*.txt) split
             into overlapping chunks, with source_key / url / jurisdiction
             metadata so retrieved chunks can always be traced to the page
             they came from.

Embeddings use ChromaDB's default embedding function (all-MiniLM-L6-v2 via
ONNX, downloaded on first run). Re-running the script rebuilds both
collections from scratch, so it always reflects the current seed fixtures
and scraped corpus.

Usage:
    python rag/build_vector_db.py            # build / rebuild
    python rag/build_vector_db.py --query "CGT when leaving Australia"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from seed_rules import RULE_FIXTURES      # noqa: E402
from seed_sources import SOURCE_FIXTURES  # noqa: E402

DB_DIR = Path(__file__).resolve().parent / "chroma_db"
SCRAPED_DIR = Path(__file__).resolve().parent / "scraped"
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def chunk_text(text: str) -> list[str]:
    """Split on paragraph boundaries into ~CHUNK_SIZE chunks with overlap."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if current and len(current) + len(para) + 1 > CHUNK_SIZE:
            chunks.append(current)
            current = current[-CHUNK_OVERLAP:] if CHUNK_OVERLAP else ""
        current = f"{current}\n{para}" if current else para
    if current:
        chunks.append(current)
    return chunks


def build() -> None:
    client = chromadb.PersistentClient(path=str(DB_DIR))
    source_meta = {s["key"]: s for s in SOURCE_FIXTURES}

    # ── rules collection ─────────────────────────────────────────────────────
    for name in ("rules", "sources"):
        try:
            client.delete_collection(name)
        except Exception:
            pass

    rules_col = client.create_collection("rules", metadata={"hnsw:space": "cosine"})
    ids, docs, metas = [], [], []
    for r in RULE_FIXTURES:
        src = source_meta[r["source_key"]]
        doc = (
            f"[{r['rule_code']}] ({r['jurisdiction']} / {r['category'].value}) "
            f"{r['description']} Reference: {r.get('section_reference', '')}"
        )
        ids.append(r["rule_code"])
        docs.append(doc)
        metas.append({
            "rule_code": r["rule_code"],
            "jurisdiction": r["jurisdiction"],
            "category": r["category"].value,
            "risk_level": r["risk_level"].value,
            "confidence_level": r["confidence_level"].value,
            "condition_expression": json.dumps(r["condition_expression"]),
            "section_reference": r.get("section_reference", ""),
            "source_key": r["source_key"],
            "source_title": src["title"],
            "source_url": src["url"],
        })
    rules_col.add(ids=ids, documents=docs, metadatas=metas)
    print(f"rules collection: {rules_col.count()} documents")

    # ── sources collection ───────────────────────────────────────────────────
    sources_col = client.create_collection("sources", metadata={"hnsw:space": "cosine"})
    ids, docs, metas = [], [], []
    for path in sorted(SCRAPED_DIR.glob("*.txt")):
        key = path.stem
        src = source_meta.get(key)
        if src is None:
            continue
        raw = path.read_text(encoding="utf-8")
        body = raw.split("-" * 78 + "\n", 1)[-1]  # strip the metadata header
        for i, chunk in enumerate(chunk_text(body)):
            ids.append(f"{key}::chunk{i:03d}")
            docs.append(chunk)
            metas.append({
                "source_key": key,
                "title": src["title"],
                "url": src["url"],
                "jurisdiction": src["jurisdiction"],
                "chunk_index": i,
            })
    # add in batches to stay under embedding batch limits
    for start in range(0, len(ids), 256):
        sources_col.add(
            ids=ids[start:start + 256],
            documents=docs[start:start + 256],
            metadatas=metas[start:start + 256],
        )
    print(f"sources collection: {sources_col.count()} chunks from "
          f"{len(set(m['source_key'] for m in metas))} pages")


def query(text: str, n: int = 4) -> None:
    client = chromadb.PersistentClient(path=str(DB_DIR))
    for name in ("rules", "sources"):
        col = client.get_collection(name)
        res = col.query(query_texts=[text], n_results=n)
        print(f"\n=== top {n} from '{name}' for: {text!r}")
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
            label = meta.get("rule_code") or f"{meta['source_key']}#{meta['chunk_index']}"
            print(f"  [{dist:.3f}] {label}: {doc[:140]}...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build or query the ClearPath vector DB.")
    parser.add_argument("--query", help="Run a test query instead of building.")
    parser.add_argument("-n", type=int, default=4, help="Number of results for --query.")
    args = parser.parse_args()
    if args.query:
        query(args.query, args.n)
    else:
        build()
