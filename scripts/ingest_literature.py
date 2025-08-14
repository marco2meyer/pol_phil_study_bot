#!/usr/bin/env python3
"""
Ingest course literature PDFs into OpenAI Vector Store
- Keeps MongoDB for app data and literature metadata
- Uses OpenAI hosted vector store with file_search

Usage examples:
  python ingest_literature.py --file path/to/rawls.pdf \
      --title "A Theory of Justice" --author "John Rawls" \
      --session-number 4 --session-topic "Gerechtigkeit" \
      --topics "justice,liberalism"

  python ingest_literature.py --dir path/to/pdfs --session-number 4 --session-topic "Gerechtigkeit"

  # Ingest from CSV manifest (expects a 'filename' column; files are resolved under rag/files)
  python ingest_literature.py --csv path/to/manifest.csv

Environment variables:
  OPENAI_API_KEY              Required
  OPENAI_VECTOR_STORE_ID      Optional (if absent, a new store will be created)
  MONGODB_URI                 Optional (defaults to mongodb://localhost:27017/)
"""
from __future__ import annotations

import os
import argparse
from pathlib import Path
import csv
from typing import Dict, List, Optional
from pymongo import MongoClient
from dotenv import load_dotenv

from rag.openai_vector_store import (
    get_or_create_vector_store,
    upload_file_with_attributes,
)


def get_db():
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    client = MongoClient(mongo_uri)
    return client["study_chatbot"], client


def persist_source(db, file_path: str, file_id: str, attributes: Dict[str, object], vector_store_id: str):
    sources = db["literature_sources"]
    doc = {
        "file_path": str(file_path),
        "openai_file_id": file_id,
        "vector_store_id": vector_store_id,
        "attributes": attributes,
    }
    # Upsert by file path + title if provided
    filt: Dict[str, object] = {"file_path": str(file_path)}
    if attributes.get("title"):
        filt["attributes.title"] = attributes["title"]
    sources.update_one(filt, {"$set": doc}, upsert=True)


def build_attributes(args, file_path: Path) -> Dict[str, object]:
    attrs: Dict[str, object] = {
        "title": args.title or file_path.stem,
        "author": args.author or "",
        "session_number": args.session_number,
        "session_topic": args.session_topic,
    }
    if args.topics:
        # comma-separated list to array
        topics = [t.strip() for t in args.topics.split(",") if t.strip()]
        attrs["topics"] = topics
    # You can add more, e.g., year=args.year if needed.
    return {k: v for k, v in attrs.items() if v not in (None, "")}


def build_attributes_from_row(row: Dict[str, str], file_path: Path) -> Dict[str, object]:
    """Construct attributes dict from a CSV row.

    Expected columns (case-insensitive):
      - file path
      - Title
      - Author
      - topics (comma separated)
      - session (number)
      - category (optional, e.g., lecture_slides)
    """
    # Normalize keys
    norm = {k.strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
    title = norm.get("title") or file_path.stem
    author = norm.get("author", "")
    session = norm.get("session")
    try:
        session_number = int(session) if session not in (None, "") else None
    except ValueError:
        session_number = None
    topics_val = norm.get("topics", "")
    topics = [t.strip() for t in topics_val.split(",") if t.strip()] if topics_val else None
    category = norm.get("category") or "literature"

    attrs: Dict[str, object] = {
        "title": title,
        "author": author,
        "session_number": session_number,
        "category": category,
    }
    if topics:
        attrs["topics"] = topics
    return {k: v for k, v in attrs.items() if v not in (None, "")}


def ingest_file(db, vector_store_id: str, file_path: Path, attributes: Dict[str, object]) -> None:
    print(f"Uploading to vector store: {file_path}")
    file_id, vs_file_id = upload_file_with_attributes(str(file_path), vector_store_id, attributes)
    persist_source(db, str(file_path), file_id, attributes, vector_store_id)
    print(f"✓ Uploaded {file_path.name} | file_id={file_id} | vs_file_id={vs_file_id}")


def ingest_csv(db, vector_store_id: str, csv_path: Path) -> None:
    """Read a CSV manifest and ingest each file with attributes.

    Columns (case-insensitive): filename, Title, Author, topics, session, category (optional)
    Files are resolved under '<project>/rag/files/'.
    """
    script_dir = Path(__file__).parent.resolve()
    default_base = (script_dir / "rag" / "files").resolve()
    with csv_path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Validate minimal columns
        lower_cols = {c.lower() for c in (reader.fieldnames or [])}
        required = {"filename", "title"}
        missing = required - lower_cols
        if missing:
            raise SystemExit(f"CSV missing required columns: {', '.join(sorted(missing))}")
        for i, row in enumerate(reader, start=1):
            fname = row.get("filename") or row.get("Filename")
            if not fname:
                print(f"Row {i}: skipping (no filename)")
                continue
            p = (default_base / fname).resolve()
            if not p.exists():
                print(f"Row {i}: file not found: {p}")
                continue
            attrs = build_attributes_from_row(row, p)
            ingest_file(db, vector_store_id, p, attrs)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Ingest PDFs to OpenAI Vector Store")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--file", type=str, help="Path to a single PDF file")
    g.add_argument("--dir", type=str, help="Ingest all PDFs in a directory (non-recursive)")
    g.add_argument("--csv", type=str, help="CSV manifest with columns: filename, Title, Author, topics, session, category(optional). Files are resolved under rag/files")

    parser.add_argument("--title", type=str, help="Document title")
    parser.add_argument("--author", type=str, help="Document author")
    parser.add_argument("--topics", type=str, help="Comma-separated topics tags")
    parser.add_argument("--session-number", type=int, help="Course session number")
    parser.add_argument("--session-topic", type=str, help="Course session topic")

    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set")

    # Vector store
    vector_store_id = get_or_create_vector_store(name="Politische Philosophie Literatur")
    print(f"Vector Store ID: {vector_store_id}")

    # Mongo
    db, _client = get_db()

    # Ingest single file
    if args.file:
        p = Path(args.file)
        if not p.exists():
            raise SystemExit(f"File not found: {p}")
        if p.suffix.lower() != ".pdf":
            print("Warning: non-PDF file, will upload as-is")
        attrs = build_attributes(args, p)
        ingest_file(db, vector_store_id, p, attrs)
        return

    # Ingest directory (all PDFs)
    if args.dir:
        d = Path(args.dir)
        if not d.is_dir():
            raise SystemExit(f"Not a directory: {d}")
        files: List[Path] = [p for p in d.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]
        if not files:
            print("No PDFs found.")
            return
        for p in files:
            attrs = build_attributes(args, p)
            ingest_file(db, vector_store_id, p, attrs)
        return

    # Ingest from CSV manifest
    if args.csv:
        csv_path = Path(args.csv)
        if not csv_path.exists():
            raise SystemExit(f"CSV not found: {csv_path}")
        ingest_csv(db, vector_store_id, csv_path)
        return


if __name__ == "__main__":
    main()
