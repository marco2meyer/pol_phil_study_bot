import os
import sys
import os
import pandas as pd
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# Ensure project root is on sys.path when running this file directly
# This file path: bots/phil_bot/rag/ingest_literature.py
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bots.phil_bot.rag.openai_vector_store import (
    get_or_create_vector_store,
    upload_file_with_attributes,
)


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "rag_manifest.csv"
FILES_DIR = HERE / "files"

# Load environment variables: root .env then bot-local .env.local
root_env = ROOT / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env)
bot_env_local = HERE.parent / ".env.local"  # bots/phil_bot/.env.local
if bot_env_local.exists():
    load_dotenv(dotenv_path=bot_env_local, override=True)


def row_to_attributes(row: pd.Series) -> Dict[str, object]:
    # Map CSV columns to attributes you want in the vector store per file
    attrs = {k: v for k, v in row.items() if pd.notna(v)}
    return attrs


def main():
    vs_name = os.getenv("OPENAI_VECTOR_STORE_NAME", "Literature")
    vector_store_id = get_or_create_vector_store(vs_name)

    df = pd.read_csv(MANIFEST)
    for _, row in df.iterrows():
        rel_path = str(row.get("path", "")).strip()
        if not rel_path:
            continue
        file_path = (HERE / rel_path).resolve()
        if not file_path.exists():
            print(f"Skip missing file: {file_path}")
            continue
        attrs = row_to_attributes(row)
        print(f"Uploading {file_path} with attrs={attrs}")
        upload_file_with_attributes(str(file_path), vector_store_id, attributes=attrs)

    print("Ingestion done.")


if __name__ == "__main__":
    main()
