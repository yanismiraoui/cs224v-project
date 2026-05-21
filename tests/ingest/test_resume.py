import sys
from pathlib import Path

import pytest

from recruitree.core.models import CareerClaim, EvidenceSource
from recruitree.ingest.resume import (
    ResumeClaimExtractor,
    ResumeIngestionResult,
    extract_resume_text_from_pdf,
    ingest_resume_text,
)


def test_plain_text_resume_ingestion_creates_source_and_deterministic_claims() -> None:
    text = """
    Jane Candidate
    Skills: Python, SQL, Machine Learning
    Experience
    - Built a candidate matching service in Python
    - Improved recruiter response rate by 35%
    Education
    B.S. Computer Science, Example University
    Projects
    - Created RecruiTree portfolio project
    """

    result = ingest_resume_text(text, title="Jane Resume", source_id="resume-jane")

    assert isinstance(result, ResumeIngestionResult)
    assert result.source == EvidenceSource(
        kind="resume",
        title="Jane Resume",
        extracted_text=text,
    )
    assert all(isinstance(claim, CareerClaim) for claim in result.claims)
    assert [claim.source_ids for claim in result.claims] == [["resume-jane"]] * len(result.claims)
    assert all(0.5 <= claim.confidence <= 0.7 for claim in result.claims)

    assert [claim.text for claim in result.claims] == [
        "Jane Candidate",
        "Skills: Python, SQL, Machine Learning",
        "Built a candidate matching service in Python",
        "Improved recruiter response rate by 35%",
        "B.S. Computer Science, Example University",
        "Created RecruiTree portfolio project",
    ]

    claims_by_text = {claim.text: claim for claim in result.claims}
    assert claims_by_text["Skills: Python, SQL, Machine Learning"].claim_type == "skill"
    assert claims_by_text["Built a candidate matching service in Python"].claim_type == "experience"
    assert claims_by_text["Improved recruiter response rate by 35%"].claim_type == "achievement"
    assert claims_by_text["B.S. Computer Science, Example University"].claim_type == "education"
    assert claims_by_text["Created RecruiTree portfolio project"].claim_type == "project"


def test_ingest_resume_text_ignores_empty_lines_and_numbers_claim_ids_deterministically() -> None:
    result = ingest_resume_text("\n- Python\n\n• Led migration project\n", source_id="resume-1")

    assert [claim.id for claim in result.claims] == ["resume-1-claim-1", "resume-1-claim-2"]
    assert [claim.text for claim in result.claims] == ["Python", "Led migration project"]


def test_resume_claim_extractor_interface_can_override_deterministic_fallback() -> None:
    class StaticExtractor:
        def extract_claims(self, text: str, *, source_id: str) -> list[CareerClaim]:
            return [
                CareerClaim(
                    id=f"{source_id}-llm-1",
                    claim_type="publication",
                    text=f"custom extraction for {text.strip()}",
                    source_ids=[source_id],
                    confidence=0.9,
                )
            ]

    extractor: ResumeClaimExtractor = StaticExtractor()

    result = ingest_resume_text("Published paper", source_id="resume-x", extractor=extractor)

    assert [claim.id for claim in result.claims] == ["resume-x-llm-1"]
    assert result.claims[0].claim_type == "publication"


def test_pdf_text_extraction_uses_pymupdf_when_available(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "resume.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    class FakePage:
        def __init__(self, text: str) -> None:
            self.text = text

        def get_text(self) -> str:
            return self.text

    class FakeDocument:
        def __iter__(self):
            return iter([FakePage("First page"), FakePage("Second page")])

        def close(self) -> None:
            self.closed = True

    class FakeFitz:
        @staticmethod
        def open(path: str):
            assert path == str(pdf_path)
            return FakeDocument()

    monkeypatch.setitem(sys.modules, "fitz", FakeFitz)

    assert extract_resume_text_from_pdf(pdf_path) == "First page\nSecond page"


def test_pdf_text_extraction_raises_clear_error_without_pymupdf(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pdf_path = tmp_path / "resume.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")
    monkeypatch.setitem(sys.modules, "fitz", None)

    with pytest.raises(RuntimeError, match="PyMuPDF"):
        extract_resume_text_from_pdf(pdf_path)
