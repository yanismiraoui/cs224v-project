"""Resume ingestion helpers with deterministic claim extraction fallback."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from recruitree.core.models import CareerClaim, EvidenceSource


@dataclass(frozen=True)
class ResumeIngestionResult:
    """Structured output from resume ingestion."""

    source: EvidenceSource
    claims: list[CareerClaim]


class ResumeClaimExtractor(Protocol):
    """Interface for pluggable resume claim extractors, such as future LLMs."""

    def extract_claims(self, text: str, *, source_id: str) -> list[CareerClaim]:
        """Extract career claims from resume text."""
        raise NotImplementedError


_EDUCATION_TERMS = (
    "education",
    "university",
    "college",
    "degree",
    "b.s.",
    "bs ",
    "bachelor",
    "m.s.",
    "ms ",
    "master",
    "phd",
    "gpa",
)
_PROJECT_TERMS = ("project", "portfolio", "created", "built", "developed", "launched")
_ACHIEVEMENT_TERMS = (
    "improved",
    "increased",
    "decreased",
    "reduced",
    "grew",
    "saved",
    "optimized",
    "achieved",
    "impact",
    "outcome",
    "metric",
)
_SECTION_NAMES = {
    "skills": "skill",
    "technical skills": "skill",
    "technologies": "skill",
    "education": "education",
    "projects": "project",
    "project experience": "project",
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
}
_SKILL_TOKEN_RE = re.compile(r"\b(python|sql|java|javascript|typescript|go|rust|c\+\+|machine learning|ml|ai|pytorch|tensorflow|react|aws|docker|kubernetes)\b", re.IGNORECASE)
_METRIC_RE = re.compile(r"(?:\b\d+(?:\.\d+)?\s*%|\$\s*\d|\b\d+x\b|\b\d+\s*(?:users|customers|hours|minutes|seconds|days|weeks|months)\b)", re.IGNORECASE)
ClaimType = Literal[
    "skill",
    "project",
    "experience",
    "achievement",
    "education",
    "publication",
]


def extract_resume_text_from_pdf(path: str | Path) -> str:
    """Extract text from a PDF resume using PyMuPDF when available."""

    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - exact import path varies by env
        raise RuntimeError(
            "PDF resume extraction requires PyMuPDF. Install it with `pip install PyMuPDF`."
        ) from exc

    if fitz is None:  # supports tests/environments that block the import explicitly
        raise RuntimeError(
            "PDF resume extraction requires PyMuPDF. Install it with `pip install PyMuPDF`."
        )

    document = fitz.open(str(path))
    try:
        pages = [page.get_text().strip() for page in document]
    finally:
        close = getattr(document, "close", None)
        if callable(close):
            close()

    return "\n".join(page_text for page_text in pages if page_text)


def ingest_resume_text(
    text: str,
    *,
    title: str | None = None,
    source_id: str = "resume",
    extractor: ResumeClaimExtractor | None = None,
) -> ResumeIngestionResult:
    """Ingest plain resume text into an evidence source and career claims."""

    source = EvidenceSource(kind="resume", title=title, extracted_text=text)
    claims = (
        extractor.extract_claims(text, source_id=source_id)
        if extractor is not None
        else _extract_claims_deterministically(text, source_id=source_id)
    )
    return ResumeIngestionResult(source=source, claims=claims)


def _extract_claims_deterministically(text: str, *, source_id: str) -> list[CareerClaim]:
    claims: list[CareerClaim] = []
    current_section: str | None = None

    for raw_line in text.splitlines():
        line = _clean_resume_line(raw_line)
        if not line:
            continue

        section_claim_type = _SECTION_NAMES.get(line.lower().rstrip(":"))
        if section_claim_type is not None:
            current_section = section_claim_type
            continue

        claim_type = _classify_claim(line, current_section=current_section)
        metrics = _extract_metrics(line)
        claim_number = len(claims) + 1
        claims.append(
            CareerClaim(
                id=f"{source_id}-claim-{claim_number}",
                claim_type=claim_type,
                text=line,
                skill_tags=_extract_skill_tags(line) if claim_type == "skill" else [],
                metrics=metrics,
                source_ids=[source_id],
                confidence=0.65 if metrics or claim_type in {"education", "skill"} else 0.6,
            )
        )

    return claims


def _clean_resume_line(line: str) -> str:
    stripped = line.strip()
    stripped = re.sub(r"^[\-•*‣▪]+\s*", "", stripped)
    return stripped.strip()


def _classify_claim(line: str, *, current_section: str | None) -> ClaimType:
    lower = f" {line.lower()} "

    if any(term in lower for term in _EDUCATION_TERMS):
        return "education"
    if _METRIC_RE.search(line) or any(term in lower for term in _ACHIEVEMENT_TERMS):
        return "achievement"
    if current_section == "skill" or line.lower().startswith("skills:"):
        return "skill"
    if current_section == "experience":
        return "experience"
    if current_section == "project" or any(term in lower for term in _PROJECT_TERMS):
        return "project"
    if current_section == "education":
        return "education"
    return "experience"


def _extract_skill_tags(line: str) -> list[str]:
    tags: list[str] = []
    for match in _SKILL_TOKEN_RE.finditer(line):
        tag = match.group(0).lower()
        if tag == "machine learning":
            tag = "machine learning"
        if tag not in tags:
            tags.append(tag)
    return tags


def _extract_metrics(line: str) -> list[str]:
    return [match.group(0).strip() for match in _METRIC_RE.finditer(line)]


__all__ = [
    "ResumeClaimExtractor",
    "ResumeIngestionResult",
    "extract_resume_text_from_pdf",
    "ingest_resume_text",
]
