import pytest
from pydantic import ValidationError

from recruitree.core.models import (
    CareerClaim,
    EvidenceSource,
    RoleFitReport,
    TargetRole,
)


def test_evidence_source_accepts_valid_kinds_and_optional_fields() -> None:
    source = EvidenceSource(
        kind="github",
        uri="https://github.com/example/project",
        title="Example project",
        extracted_text="Built a production data pipeline.",
    )

    assert source.kind == "github"
    assert source.uri == "https://github.com/example/project"
    assert source.title == "Example project"
    assert source.extracted_text == "Built a production data pipeline."


def test_evidence_source_rejects_unknown_kind() -> None:
    with pytest.raises(ValidationError):
        EvidenceSource(kind="linkedin")


def test_career_claim_validates_claim_type_and_confidence_bounds() -> None:
    claim = CareerClaim(
        id="claim-1",
        claim_type="skill",
        text="Built Python services for ML workflows.",
        skill_tags=["python", "ml"],
        metrics=["reduced runtime by 30%"],
        source_ids=["source-1"],
        confidence=0.95,
    )

    assert claim.id == "claim-1"
    assert claim.claim_type == "skill"
    assert claim.confidence == 0.95
    assert claim.skill_tags == ["python", "ml"]
    assert claim.metrics == ["reduced runtime by 30%"]
    assert claim.source_ids == ["source-1"]


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_career_claim_rejects_confidence_outside_zero_to_one(confidence: float) -> None:
    with pytest.raises(ValidationError):
        CareerClaim(
            id="claim-1",
            claim_type="achievement",
            text="Improved candidate matching quality.",
            confidence=confidence,
        )


def test_career_claim_rejects_unknown_claim_type() -> None:
    with pytest.raises(ValidationError):
        CareerClaim(
            id="claim-1",
            claim_type="hobby",
            text="Enjoys side projects.",
            confidence=0.5,
        )


def test_target_role_defaults_lists_independently() -> None:
    first = TargetRole(title="ML Engineer")
    second = TargetRole(organization="ExampleCo")

    first.required_skills.append("python")
    first.preferred_skills.append("langchain")
    first.responsibilities.append("ship models")
    first.success_signals.append("production impact")

    assert second.required_skills == []
    assert second.preferred_skills == []
    assert second.responsibilities == []
    assert second.success_signals == []


def test_role_fit_report_nests_target_and_claims() -> None:
    target = TargetRole(
        title="AI Engineer",
        required_skills=["python"],
        preferred_skills=["pydantic"],
        responsibilities=["build applied AI products"],
        success_signals=["deployed user-facing features"],
    )
    claim = CareerClaim(
        id="claim-1",
        claim_type="project",
        text="Created an evidence-backed recruiting assistant.",
        skill_tags=["python", "pydantic"],
        confidence=0.9,
    )

    report = RoleFitReport(
        target=target,
        matched_claims=[claim],
        missing_signals=["enterprise deployment"],
        strongest_positioning=["strong applied AI portfolio"],
        risks=["limited explicit enterprise evidence"],
        recommended_assets=["case study"],
    )

    assert report.target == target
    assert report.matched_claims == [claim]
    assert report.missing_signals == ["enterprise deployment"]
    assert report.strongest_positioning == ["strong applied AI portfolio"]
    assert report.risks == ["limited explicit enterprise evidence"]
    assert report.recommended_assets == ["case study"]


def test_role_fit_report_requires_nested_target_model() -> None:
    with pytest.raises(ValidationError):
        RoleFitReport(
            target=None,
            matched_claims=[],
            missing_signals=[],
            strongest_positioning=[],
            risks=[],
            recommended_assets=[],
        )
