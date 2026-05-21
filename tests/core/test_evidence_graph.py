from typing import Literal

from recruitree.core.evidence_graph import EvidenceGraph
from recruitree.core.models import CareerClaim, EvidenceSource

ClaimType = Literal[
    "skill",
    "project",
    "experience",
    "achievement",
    "education",
    "publication",
]


def claim(
    claim_id: str,
    text: str,
    *,
    claim_type: ClaimType = "skill",
    skill_tags: list[str] | None = None,
    metrics: list[str] | None = None,
    source_ids: list[str] | None = None,
    confidence: float = 0.7,
) -> CareerClaim:
    return CareerClaim(
        id=claim_id,
        claim_type=claim_type,
        text=text,
        skill_tags=skill_tags or [],
        metrics=metrics or [],
        source_ids=source_ids or [],
        confidence=confidence,
    )


def test_adds_claims_from_resume_and_github_sources() -> None:
    graph = EvidenceGraph()
    resume_id = graph.add_source(
        EvidenceSource(kind="resume", uri="file://resume.pdf", title="Resume")
    )
    github_id = graph.add_source(
        EvidenceSource(kind="github", uri="https://github.com/user/project", title="Project")
    )

    added = graph.add_claims(
        [
            claim(
                "resume-python",
                "Built production Python data services.",
                skill_tags=["Python"],
                source_ids=[resume_id],
            ),
            claim(
                "github-python",
                "Maintained an open-source ML package.",
                claim_type="project",
                skill_tags=["Python", "ML"],
                source_ids=[github_id],
            ),
        ]
    )

    assert len(added) == 2
    assert [stored.id for stored in graph.claims] == ["resume-python", "github-python"]
    assert graph.claims[0].source_ids == [resume_id]
    assert graph.claims[1].source_ids == [github_id]


def test_duplicate_claims_merge_by_normalized_text_and_skill_tags() -> None:
    graph = EvidenceGraph()

    first = graph.add_claim(
        claim(
            "resume-claim",
            "Built production Python data services.",
            skill_tags=["Python", "Data Engineering"],
            metrics=["served 1M requests"],
            source_ids=["resume"],
            confidence=0.6,
        )
    )
    merged = graph.add_claim(
        claim(
            "github-claim",
            "  built   production python data services  ",
            skill_tags=["data engineering", "python"],
            metrics=["served 1M requests", "cut latency 25%"],
            source_ids=["github", "resume"],
            confidence=0.9,
        )
    )

    assert merged is first
    assert len(graph.claims) == 1
    assert graph.claims[0].id == "resume-claim"
    assert graph.claims[0].text == "Built production Python data services."
    assert graph.claims[0].skill_tags == ["Python", "Data Engineering"]
    assert graph.claims[0].metrics == ["served 1M requests", "cut latency 25%"]
    assert graph.claims[0].source_ids == ["resume", "github"]
    assert graph.claims[0].confidence == 0.9


def test_same_text_with_different_skill_tags_remains_distinct() -> None:
    graph = EvidenceGraph()

    graph.add_claim(claim("python", "Built APIs.", skill_tags=["Python"]))
    graph.add_claim(claim("go", "built apis", skill_tags=["Go"]))

    assert [stored.id for stored in graph.claims] == ["python", "go"]


def test_source_provenance_is_preserved_in_to_dict() -> None:
    graph = EvidenceGraph()
    resume_id = graph.add_source(EvidenceSource(kind="resume", title="Resume"), "resume-main")
    github_id = graph.add_source(EvidenceSource(kind="github", title="GitHub"), "github-main")

    graph.add_claim(
        claim(
            "claim-1",
            "Shipped recruiter tooling.",
            skill_tags=["Python"],
            source_ids=[resume_id],
            confidence=0.5,
        )
    )
    graph.add_claim(
        claim(
            "claim-2",
            "shipped recruiter tooling",
            skill_tags=["python"],
            source_ids=[github_id],
            confidence=0.8,
        )
    )

    serialized = graph.to_dict()

    assert serialized["sources"] == {
        "resume-main": {"kind": "resume", "uri": None, "title": "Resume", "extracted_text": None},
        "github-main": {"kind": "github", "uri": None, "title": "GitHub", "extracted_text": None},
    }
    assert len(serialized["claims"]) == 1
    assert serialized["claims"][0]["source_ids"] == ["resume-main", "github-main"]
    assert serialized["claims"][0]["confidence"] == 0.8
