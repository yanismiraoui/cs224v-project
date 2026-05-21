# RecruiTree V2 Rebuild Plan

**Goal:** Rebuild RecruiTree from a resume-to-website demo into a genuinely useful career operating system that turns a person’s raw evidence — resume, GitHub, projects, writing, job descriptions — into verified, role-specific career assets.

**Architecture:** Start with a clean, testable core that separates data ingestion, profile intelligence, asset generation, review/scoring, and publishing. Keep the product simple at first: a local-first web app with a deterministic pipeline, structured outputs, previewable artifacts, and human approval before publishing.

**Tech Stack:** Python, FastAPI or Streamlit for the first UI, Pydantic models, pytest, optional LangChain/LangGraph only where orchestration helps, GitHub API, PDF parsing, static artifact generation, and provider-agnostic LLM adapters.

---

## 1. What the current project is

The current `cs224v-project` repo is a Streamlit + LangChain/Together AI prototype called **RecruiTree**. It can:

- Parse uploaded resume PDFs.
- Chat with a job-application assistant.
- Generate personal portfolio website files.
- Generate and publish GitHub profile READMEs.
- Attempt GitHub Pages publishing.
- Collect feedback into Postgres.

## 2. Main limitations to fix

- **Too prompt-driven:** most behavior depends on large fragile prompts and string parsing.
- **Weak product loop:** it creates content, but does not help users decide what career story is strongest.
- **No evidence model:** resume/GitHub/job-description facts are not normalized into reusable structured data.
- **Risky publishing:** publishing flows need clearer preview, diff, approval, and rollback.
- **Tight coupling:** Streamlit UI, database, file generation, LLM calls, and GitHub publishing are mixed together.
- **Provider lock-in:** Together-specific wrapper and secrets layout are hardcoded.
- **No tests:** no reliable way to change the product safely.
- **Generic outputs:** generated assets risk looking like every other AI portfolio.

## 3. New product direction: “career proof engine”

Instead of “make me a portfolio,” the product should answer:

> “What is the most credible, differentiated version of my professional story for this exact opportunity, and can you generate the artifacts that prove it?”

### Core idea

Build a **Career Proof Engine** that collects evidence, maps it to target roles, finds story gaps, and generates assets grounded in verifiable proof.

### Differentiators

1. **Evidence-first career graph**
   - Extract claims from resumes, GitHub repos, papers, websites, LinkedIn text, and manual notes.
   - Store claims as structured objects: skill, project, outcome, metric, evidence source, confidence.

2. **Role-fit lens**
   - User provides a job description, school application prompt, lab opening, startup role, etc.
   - The system maps required signals to the user’s existing evidence.
   - It shows strengths, gaps, missing proof, and suggested projects/content.

3. **Portfolio as proof, not decoration**
   - Generate a website around evidence cards, project timelines, demos, metrics, and source links.
   - Every claim should trace back to a source.

4. **Asset studio**
   - Generate multiple career assets from the same structured graph:
     - personal website
     - GitHub profile README
     - project READMEs
     - role-specific resume bullets
     - cold email / recruiter message
     - interview talking points

5. **Critic and originality layer**
   - Score assets for specificity, proof, differentiation, ATS fit, overclaiming, and cliché density.
   - Reject generic AI output and force improvements.

6. **Human approval and safe publishing**
   - Preview generated files.
   - Show diffs before publishing.
   - Require explicit approval for GitHub writes.
   - Keep rollback snapshots.

## 4. Proposed MVP scope

### MVP user flow

1. User uploads a resume PDF or pastes resume text.
2. User connects or pastes GitHub profile/repo links.
3. User pastes a target job/opportunity description.
4. App builds a structured career evidence graph.
5. App shows:
   - strongest proof points
   - weak/generic claims
   - missing evidence for the target role
   - recommended positioning
6. User chooses assets to generate.
7. App generates previewable artifacts.
8. App runs a critic pass and suggests edits.
9. User approves final version.
10. Optional: publish to GitHub Pages/profile repo.

### MVP assets

- `career_graph.json`
- role-fit report markdown
- portfolio website static files
- GitHub profile README
- target-specific resume bullet suggestions

## 5. Clean repo structure

```text
recruitree/
  app/
    main.py                    # FastAPI/Streamlit entrypoint
    ui/                        # UI components
  recruitree/
    core/
      models.py                # Pydantic domain models
      evidence_graph.py        # claim normalization + merge logic
      scoring.py               # deterministic scoring helpers
    ingest/
      resume.py                # PDF/text resume parsing
      github.py                # GitHub repo/profile ingestion
      job_description.py       # target role parsing
    llm/
      client.py                # provider-agnostic LLM interface
      prompts/                 # prompt templates only, no business logic
    generate/
      website.py               # portfolio generator
      readme.py                # GitHub README generator
      resume_bullets.py        # bullet generator
      messages.py              # recruiter/cold email generator
    review/
      critic.py                # specificity/proof/originality checks
      diff.py                  # artifact diffs
    publish/
      github_pages.py          # safe publishing
      github_profile.py        # safe profile README publishing
  tests/
    core/
    ingest/
    generate/
    review/
  docs/
    plans/
    product/
  pyproject.toml
  README.md
```

## 6. Domain models first

Create Pydantic models before UI work:

```python
class EvidenceSource(BaseModel):
    kind: Literal["resume", "github", "manual", "job_description", "website"]
    uri: str | None = None
    title: str | None = None
    extracted_text: str | None = None

class CareerClaim(BaseModel):
    id: str
    claim_type: Literal["skill", "project", "experience", "achievement", "education", "publication"]
    text: str
    skill_tags: list[str] = []
    metrics: list[str] = []
    source_ids: list[str] = []
    confidence: float = Field(ge=0, le=1)

class TargetRole(BaseModel):
    title: str | None = None
    organization: str | None = None
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    responsibilities: list[str] = []
    success_signals: list[str] = []

class RoleFitReport(BaseModel):
    target: TargetRole
    matched_claims: list[CareerClaim]
    missing_signals: list[str]
    strongest_positioning: list[str]
    risks: list[str]
    recommended_assets: list[str]
```

## 7. Implementation tasks

### Task 1: Freeze the old prototype and document baseline

**Objective:** Preserve the existing project as reference while making it clear V2 is a rebuild.

**Files:**
- Create: `docs/product/current-state.md`
- Modify: `README.md`

**Steps:**
1. Write a current-state summary from the existing code.
2. Add a V2 note to README explaining that the prototype is being rebuilt.
3. Run `git diff` and verify only docs changed.
4. Commit: `docs: document RecruiTree v1 baseline`.

### Task 2: Add modern Python project scaffolding

**Objective:** Replace the flat script-style prototype with a testable package structure.

**Files:**
- Create: `pyproject.toml`
- Create directories from the proposed structure.
- Create: `tests/test_smoke.py`

**Steps:**
1. Add package metadata and dependencies.
2. Add pytest configuration.
3. Add an import smoke test.
4. Run `python -m pytest`.
5. Commit: `chore: add v2 project scaffold`.

### Task 3: Implement core domain models

**Objective:** Define structured career evidence models.

**Files:**
- Create: `recruitree/core/models.py`
- Create: `tests/core/test_models.py`

**Steps:**
1. Write failing tests for `CareerClaim`, `EvidenceSource`, `TargetRole`, and `RoleFitReport` validation.
2. Implement the models.
3. Run `python -m pytest tests/core/test_models.py -v`.
4. Commit: `feat: add career evidence domain models`.

### Task 4: Build deterministic evidence graph merge logic

**Objective:** Combine extracted claims from multiple sources without duplicates.

**Files:**
- Create: `recruitree/core/evidence_graph.py`
- Create: `tests/core/test_evidence_graph.py`

**Steps:**
1. Test adding claims from resume and GitHub.
2. Test duplicate merging by normalized text + skill tags.
3. Test source provenance preservation.
4. Implement minimal merge logic.
5. Commit: `feat: add evidence graph merge logic`.

### Task 5: Add resume ingestion

**Objective:** Extract text and basic structured claims from PDF/text resumes.

**Files:**
- Create: `recruitree/ingest/resume.py`
- Create: `tests/ingest/test_resume.py`

**Steps:**
1. Test plain text resume extraction into source + claims.
2. Test PDF text extraction with a fixture later.
3. Keep LLM extraction behind an interface; add a deterministic fallback.
4. Commit: `feat: add resume ingestion pipeline`.

### Task 6: Add target role parser

**Objective:** Parse job descriptions into `TargetRole` objects.

**Files:**
- Create: `recruitree/ingest/job_description.py`
- Create: `tests/ingest/test_job_description.py`

**Steps:**
1. Test extraction of title, skills, responsibilities, and success signals from sample text.
2. Implement deterministic keyword extraction first.
3. Add optional LLM parser later.
4. Commit: `feat: add target role parsing`.

### Task 7: Add role-fit scoring

**Objective:** Match user evidence against target role requirements.

**Files:**
- Create: `recruitree/core/scoring.py`
- Create: `tests/core/test_scoring.py`

**Steps:**
1. Test exact skill matches.
2. Test missing required skills.
3. Test strongest-positioning output.
4. Implement simple transparent scoring.
5. Commit: `feat: add transparent role-fit scoring`.

### Task 8: Add artifact generation interfaces

**Objective:** Generate outputs from structured data, not raw prompts.

**Files:**
- Create: `recruitree/generate/readme.py`
- Create: `recruitree/generate/website.py`
- Create: `tests/generate/test_readme.py`
- Create: `tests/generate/test_website.py`

**Steps:**
1. Test README generation from a small `RoleFitReport` fixture.
2. Test website output includes evidence-backed sections.
3. Implement deterministic templates first.
4. Add LLM-enhanced mode later.
5. Commit: `feat: generate evidence-backed career assets`.

### Task 9: Add critic pass

**Objective:** Prevent generic, unsupported, or overclaimed content.

**Files:**
- Create: `recruitree/review/critic.py`
- Create: `tests/review/test_critic.py`

**Steps:**
1. Test cliché detection.
2. Test unsupported claim detection.
3. Test specificity score.
4. Commit: `feat: add career asset critic`.

### Task 10: Add preview UI

**Objective:** Let the user inspect graph, role-fit report, generated assets, and critic feedback.

**Files:**
- Create or modify: `app/main.py`
- Create: `app/ui/*`

**Steps:**
1. Build simple upload/paste inputs.
2. Show evidence graph table.
3. Show target role-fit report.
4. Show generated artifacts in tabs.
5. No publishing yet.
6. Commit: `feat: add RecruiTree v2 preview UI`.

### Task 11: Add safe publishing

**Objective:** Publish only after explicit human approval.

**Files:**
- Create: `recruitree/publish/github_profile.py`
- Create: `recruitree/publish/github_pages.py`
- Create: `recruitree/review/diff.py`
- Create: `tests/publish/test_github_profile.py`

**Steps:**
1. Add dry-run mode.
2. Show before/after diffs.
3. Require explicit approval flag.
4. Store rollback snapshot.
5. Commit: `feat: add safe GitHub publishing workflow`.

## 8. Design principles

- Evidence before aesthetics.
- Deterministic core, LLM-enhanced edges.
- Preview before publish.
- Every generated claim should be traceable.
- Useful even without a perfect LLM response.
- Boring tests, original product.

## 9. Initial success criteria

- A user can create a role-fit report from resume + job description.
- Generated assets contain verifiable claims and avoid generic filler.
- The app works locally without publishing credentials.
- Tests cover core parsing, scoring, generation, and critic logic.
- Publishing requires preview, diff, and approval.

## 10. Open product questions

- Should the first UI stay Streamlit for speed, or move to FastAPI + a richer frontend?
- Should GitHub ingestion use authenticated API only, or support public scraping fallback?
- Should V2 live in this repo on a branch, or should we create a new clean repo once the scaffold is stable?
- What is the first target persona: students, researchers, developers, founders, or job switchers?
