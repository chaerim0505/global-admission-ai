"""config/rag.yaml 로더. 검색 파라미터를 코드에 박지 않는다."""

from functools import lru_cache
from pathlib import Path

import yaml


RAG_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "rag.yaml"


@lru_cache(maxsize=1)
def load_rag_config(path: Path = RAG_CONFIG_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def retrieval_top_k() -> int:
    return int(load_rag_config().get("retrieval", {}).get("top_k", 5))


def min_evidence() -> int:
    return int(load_rag_config().get("retrieval", {}).get("min_evidence", 1))
