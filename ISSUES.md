# Documentation Issues for StacksOrbit

This document lists the identified issues in the StacksOrbit documentation.

## 1. Ambiguity

*   **Inconsistent Commands (historical, largely resolved):** Earlier versions of the documentation (including legacy `README_ENHANCED.md` and `README_ULTIMATE.md`) presented multiple overlapping commands for similar actions, such as `npm run setup` and `python setup_wizard.py`, without clear guidance on when to use each. The current `README.md` and `AGENTS.md` now standardize on the `stacksorbit_cli.py` entry point and should be treated as canonical, while the legacy READMEs are retained as extended background.
*   **Vague "Ultimate" and "Enhanced" Terminology (legacy docs):** The project historically used terms like "ultimate" and "enhanced" (e.g., `ultimate_stacksorbit.py`, `enhanced_dashboard.py`) without a clear definition of what makes them "ultimate" or "enhanced" compared to their counterparts. These labels are now considered legacy; `AGENTS.md` and `stacksorbit_cli.py` describe the current, unified toolchain.

## 2. Contradictions

*   **Redundant and Potentially Conflicting Information:** There is significant overlap between the `README.md`, `ENHANCEMENT_SUMMARY.md`, and `CONTRIBUTING.md` files. This creates a risk of information becoming inconsistent across documents as the project evolves.

## 3. Missing Elements

*   **No `AGENTS.md` File (resolved):** This issue has been addressed. `AGENTS.md` now exists and serves as the primary reference for both human developers and AI agents.
*   **Lack of a Clear "Single Source of Truth" (resolved):** The creation of `AGENTS.md` and the simplified root `README.md` established a clear "single source of truth" for development and deployment information. Other READMEs are now secondary and should defer to `AGENTS.md`.
*   **No High-Level Architectural Overview (resolved):** The high-level architecture, including the relationship between the CLI, core deployer, monitoring dashboard, and the Stacks blockchain, is now documented in `AGENTS.md` (see section 1.1 Architectural Overview).

## 4. Scalability Concerns

*   **Documentation Maintenance Overhead:** The current fragmented and redundant documentation structure is difficult to maintain. As the project grows, keeping all documents in sync will become increasingly challenging.

## 5. Compliance Gaps

*   **No Explicit License Information in all Files:** While a `LICENSE` file exists, not every file includes a license header, which can be a good practice for open-source projects.
