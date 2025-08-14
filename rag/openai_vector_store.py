from __future__ import annotations
import os
from typing import Dict, List, Optional
from openai import OpenAI


def get_openai_client() -> OpenAI:
    """Create an OpenAI client honoring OPENAI_API_KEY."""
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_or_create_vector_store(name: Optional[str] = None) -> str:
    """Return an existing vector store id from env or create a new one.

    Priority:
      1) OPENAI_VECTOR_STORE_ID env var
      2) Create a new vector store with optional name
    """
    vs_id = os.getenv("OPENAI_VECTOR_STORE_ID")
    if vs_id:
        return vs_id

    client = get_openai_client()
    vs = client.vector_stores.create(name=name or "Course Literature")
    return vs.id


def upload_file_with_attributes(
    file_path: str,
    vector_store_id: str,
    attributes: Optional[Dict[str, object]] = None,
) -> tuple[str, str]:
    """Upload a single file to a vector store with optional attributes.

    Returns a tuple: (file_id, vector_store_file_id).
    The `file_id` is referenced by OpenAI annotations (e.g., file citations),
    while the `vector_store_file_id` represents the indexed object inside the vector store.
    """
    client = get_openai_client()

    # First upload as a generic file
    f = client.files.create(file=open(file_path, "rb"), purpose="assistants")

    # Then attach to vector store with attributes
    vs_file = client.vector_stores.files.create(
        vector_store_id=vector_store_id,
        file_id=f.id,
        attributes=attributes or {},
    )
    return f.id, vs_file.id


def upload_batch(
    files: List[str],
    vector_store_id: str,
    attributes_list: Optional[List[Dict[str, object]]] = None,
) -> List[str]:
    """Upload multiple files; attributes_list aligns with files (or empty dicts)."""
    client = get_openai_client()

    # Upload all to Files
    file_ids: List[str] = []
    for p in files:
        f = client.files.create(file=open(p, "rb"), purpose="assistants")
        file_ids.append(f.id)

    # Attach to vector store as a batch
    vsf = client.vector_stores.file_batches.create_and_poll(
        vector_store_id=vector_store_id,
        file_ids=file_ids,
    )

    # Optional: per-file attributes can be applied by updating each file record
    if attributes_list:
        for idx, f_id in enumerate(file_ids):
            attrs = attributes_list[idx] if idx < len(attributes_list) else {}
            try:
                client.vector_stores.files.update(
                    vector_store_id=vector_store_id,
                    file_id=f_id,
                    attributes=attrs,
                )
            except Exception:
                # If update not supported in your SDK version, fall back to create per-file call
                client.vector_stores.files.create(
                    vector_store_id=vector_store_id,
                    file_id=f_id,
                    attributes=attrs,
                )

    return file_ids
