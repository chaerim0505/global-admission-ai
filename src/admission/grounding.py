"""Retrieve stored official evidence for admission candidates."""

from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl, TypeAdapter

from admission.official_sources import is_allowed_source, load_allowed_hosts


EVIDENCE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "evidence_chunks.json"
)


class EvidenceChunk(BaseModel):
    """A passage from an official source linked to one candidate."""

    programId: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    text: str = Field(min_length=1)
    sourceUrl: HttpUrl
    checkedAt: date


def retrieve_candidate_evidence(
    candidates: Iterable[Mapping[str, object]],
    interests: Sequence[str] = (),
    *,
    top_k: int = 5,
    path: Path | None = None,
) -> dict[str, list[dict[str, object]]]:
    """Return up to five official evidence chunks per candidate."""

    candidate_ids = {
        program_id
        for candidate in candidates
        if isinstance(program_id := candidate.get("programId"), str)
        and program_id
    }
    limit = max(0, min(top_k, 5))
    if not candidate_ids or limit == 0:
        return {}

    evidence_path = EVIDENCE_PATH if path is None else path
    try:
        raw = evidence_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}

    chunks = TypeAdapter(list[EvidenceChunk]).validate_json(raw)
    hosts = load_allowed_hosts()
    keywords = [interest.strip().casefold() for interest in interests if interest.strip()]

    def priority(chunk: EvidenceChunk) -> tuple[bool, date]:
        """Prefer interest matches, then more recently checked evidence."""
        searchable = f"{chunk.topic} {chunk.text}".casefold()
        return any(keyword in searchable for keyword in keywords), chunk.checkedAt

    results: dict[str, list[dict[str, object]]] = {}
    seen_topics: dict[str, set[str]] = {}

    for chunk in sorted(chunks, key=priority, reverse=True):
        program_id = chunk.programId
        if program_id not in candidate_ids:
            continue
        if not is_allowed_source(str(chunk.sourceUrl), hosts):
            continue

        evidence = results.setdefault(program_id, [])
        topics = seen_topics.setdefault(program_id, set())
        topic = chunk.topic.strip().casefold()
        if len(evidence) >= limit or topic in topics:
            continue

        evidence.append(chunk.model_dump(mode="json"))
        topics.add(topic)

    return results