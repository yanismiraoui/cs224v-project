"""Deterministic merge container for career evidence claims."""

from collections.abc import Iterable
import re
import string

from recruitree.core.models import CareerClaim, EvidenceSource

_WHITESPACE_RE = re.compile(r"\s+")
_EDGE_PUNCTUATION = string.punctuation + "\u201c\u201d\u2018\u2019"


class EvidenceGraph:
    """A small evidence graph that deduplicates equivalent career claims.

    Claims are considered duplicates when their normalized text and normalized
    skill tag set match. Merging preserves the first claim's identity and text,
    appending unique provenance and metrics deterministically in first-seen order.
    """

    def __init__(self) -> None:
        self.sources: dict[str, EvidenceSource] = {}
        self.claims: list[CareerClaim] = []
        self._claim_index: dict[tuple[str, tuple[str, ...]], CareerClaim] = {}

    def add_source(self, source: EvidenceSource, source_id: str | None = None) -> str:
        """Add an evidence source and return its deterministic source id."""
        resolved_id = source_id or self._next_source_id()
        self.sources[resolved_id] = source
        return resolved_id

    def add_claim(self, claim: CareerClaim) -> CareerClaim:
        """Add a claim, merging into an existing equivalent claim when present."""
        key = self._claim_key(claim)
        existing = self._claim_index.get(key)
        if existing is None:
            self.claims.append(claim)
            self._claim_index[key] = claim
            return claim

        self._merge_claim(existing, claim)
        return existing

    def add_claims(self, claims: Iterable[CareerClaim]) -> list[CareerClaim]:
        """Add multiple claims, returning the stored claim for each input claim."""
        return [self.add_claim(claim) for claim in claims]

    def to_dict(self) -> dict[str, object]:
        """Serialize the graph in deterministic insertion order."""
        return {
            "sources": {
                source_id: self._dump_model(source)
                for source_id, source in self.sources.items()
            },
            "claims": [self._dump_model(claim) for claim in self.claims],
        }

    def _next_source_id(self) -> str:
        index = len(self.sources) + 1
        candidate = f"source-{index}"
        while candidate in self.sources:
            index += 1
            candidate = f"source-{index}"
        return candidate

    @classmethod
    def _claim_key(cls, claim: CareerClaim) -> tuple[str, tuple[str, ...]]:
        return (
            cls._normalize_text(claim.text),
            tuple(sorted({cls._normalize_skill_tag(tag) for tag in claim.skill_tags})),
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        words = []
        for word in _WHITESPACE_RE.split(text.strip().lower()):
            stripped = word.strip(_EDGE_PUNCTUATION)
            if stripped:
                words.append(stripped)
        return " ".join(words)

    @staticmethod
    def _normalize_skill_tag(tag: str) -> str:
        return _WHITESPACE_RE.sub(" ", tag.strip().lower())

    @staticmethod
    def _merge_claim(existing: CareerClaim, incoming: CareerClaim) -> None:
        for source_id in incoming.source_ids:
            if source_id not in existing.source_ids:
                existing.source_ids.append(source_id)

        for metric in incoming.metrics:
            if metric not in existing.metrics:
                existing.metrics.append(metric)

        existing.confidence = max(existing.confidence, incoming.confidence)

    @staticmethod
    def _dump_model(model: CareerClaim | EvidenceSource) -> dict[str, object]:
        return model.model_dump()


__all__ = ["EvidenceGraph"]
