# RecruiTree V1 Current State

This document captures the baseline of the existing RecruiTree prototype before the V2 rebuild. It is intended as a reference point, not as the target architecture for future work.

## Summary

RecruiTree V1 is a Streamlit + LangChain/Together AI prototype for helping users create professional online presence and job-application materials. The app centers on a conversational assistant that can use uploaded resume PDF text, generate portfolio website files, generate GitHub profile README content, publish to GitHub surfaces, and collect user feedback.

## Repository shape

- `README.md` — original project overview and Streamlit run instructions.
- `requirements.txt` — pinned Python dependencies for the prototype.
- `cv_examples/` — sample resume PDF assets.
- `langchain_agents/` — Streamlit UI, LangChain agent, Together AI wrapper, generation tools, website page generators, and feedback analytics page.

## Runtime and dependencies

- UI: Streamlit (`langchain_agents/streamlit_app.py`).
- Agent orchestration: LangChain structured chat agent with conversation memory (`langchain_agents/agent.py`).
- LLM provider: Together AI through a custom LangChain `LLM` wrapper (`langchain_agents/custom_together_llm.py`).
- Resume extraction: PyMuPDF reads uploaded PDFs into text.
- GitHub integration: PyGithub for reading/writing profile repositories and GitHub Pages repositories.
- Feedback storage: PostgreSQL via `psycopg2`.
- Analytics: Streamlit + pandas + Plotly feedback dashboard.
- Secrets: root-level `secrets.toml` is expected to contain at least `TOGETHER_API_KEY` and `POSTGRES_DB`.

## User-facing app flow

1. The user starts `langchain_agents/streamlit_app.py` with Streamlit.
2. The app loads Together AI and Postgres credentials from `secrets.toml`.
3. A unique session user id and `JobApplicationAgent` are initialized in Streamlit session state.
4. The user can upload:
   - a resume PDF, parsed with PyMuPDF;
   - a profile picture, saved into temporary/static image locations.
5. The main `Chat` tab lets the user ask for portfolio websites, GitHub profile help, or README generation.
6. The `Preview` tab loads generated files from `temp/` and displays HTML/CSS/JS or README output.
7. The `Feedback Analytics` tab reads Postgres feedback rows and renders ratings, timelines, and recent examples.

## Agent and tool behavior

The `JobApplicationAgent` wraps a Together AI model in a LangChain structured chat agent. Available tools include:

- `route_website_request` — routes website requests to page generators and writes generated website assets.
- `optimize_github_profile` — scrapes/parses a GitHub profile page and returns improvement advice.
- `generate_github_readme` — creates a GitHub profile README from resume content and optional instructions.
- `get_current_github_readme` — fetches the current profile README from the authenticated user's profile repo.
- `publish_to_github_readme` — creates or updates the authenticated user's profile README.
- `publish_to_github_pages` — creates/updates a `<username>.github.io` repo and uploads generated files from `temp/`.

Tool calls are logged to an in-memory action history and to timestamped files under `logs/`.

## Generated artifacts

The prototype primarily writes generated artifacts into `temp/`:

- `index.html`
- `style.css`
- `script.js`
- `README.md`
- image assets under `temp/imgs/`
- routed page assets such as `navigation.html`, `navigation.css`, `navigation.js`, `shared.css`, `shared.js`, `education.html`, and `education.js`

The preview page reads these files and can package the temp directory as a ZIP download.

## Website generation implementation

There are two overlapping website-generation paths:

1. `generate_website_content` in `tools.py`, which prompts the LLM to return HTML/CSS/JS code blocks and writes them directly into `temp/`.
2. A routed page-generation system under `langchain_agents/agents/`, with generators for shared site elements, home screen content, and education pages. It uses singleton state for shared resume content, navigation, CSS, and JavaScript.

Both paths are prompt-driven and depend on the model returning parseable content in the expected format.

## GitHub and publishing behavior

The prototype can use a user-provided GitHub token to:

- infer the authenticated username;
- read the profile README from a profile repo named after the username;
- create/update a profile README in that repo;
- create/get a `<username>.github.io` repository;
- upload local `temp/` files into the GitHub Pages repo.

These flows directly write to GitHub when invoked. There is no dedicated dry-run, diff, explicit approval checkpoint, or rollback snapshot in the current implementation.

## Feedback behavior

Assistant responses expose Streamlit feedback controls. Submitted feedback is written to a Postgres table named `agent_feedback` with timestamp, user id, chat history, user input, agent response, rating, and free-text feedback. The analytics page reads this table and displays aggregate metrics and recent feedback.

## V1 limitations to preserve as rebuild context

- The core product behavior is largely prompt-driven with limited structured domain models.
- Resume data, GitHub data, generated claims, and target-role information are not normalized into a reusable evidence graph.
- UI, LLM calls, file generation, database behavior, GitHub publishing, and app state are tightly coupled.
- The LLM provider and secrets layout are Together-specific.
- Generated outputs are parsed from expected string/code-block formats, which is fragile.
- Publishing can make direct GitHub changes without a preview/diff/approval/rollback workflow.
- There is no test suite protecting the current behavior.
- Temporary output directories, singleton generator state, and session state make behavior difficult to reproduce.

## V2 implication

V2 should treat this implementation as a working product reference and demo baseline. The rebuild should keep the useful user outcomes — resume ingestion, career asset generation, previews, GitHub assets, publishing, and feedback — while replacing the architecture with a testable, evidence-first pipeline and safer human-approved publishing flow.
