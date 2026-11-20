# A11yCoach — Software Requirements

## 1. Functional Requirements (FR)

### FR-01 — Accessibility Issue Input
The system must accept an accessibility issue description from a user through an API request.

### FR-02 — WCAG Criterion Mapping
The system must map a submitted accessibility issue to relevant WCAG 2.2 success criteria using available reference data.

### FR-03 — Criterion Details
The system must return the criterion ID, title, conformance level, and explanation when available.

### FR-04 — Fix Recommendations
The system must provide actionable recommendations for fixing an accessibility issue, based on trusted W3C guidance.

### FR-05 — Unknown Information Handling
The system must clearly indicate when it cannot confidently map an issue or when supporting information is unavailable, instead of inventing a response.

---

## 2. Non-Functional Requirements (NFR)

### NFR-01 — Performance
The API should respond to standard requests within 2 seconds for at least 95% of requests under normal local development conditions.

### NFR-02 — Reliability
The API must return valid JSON responses and appropriate HTTP status codes for at least 99% of valid test requests in the automated test suite.

### NFR-03 — Maintainability
The project must follow consistent Python formatting and linting rules using Ruff, with no lint errors in the project code.

### NFR-04 — Security
The API must not expose secrets, credentials, or private configuration in source control or API responses.

### NFR-05 — Testability
The core mapping logic and API endpoints must be covered by automated tests using pytest, with at least 80% code coverage as a target when coverage measurement is configured.

---

## 3. Constraints

- Python 3.12 or newer.
- FastAPI for the API layer.
- WCAG 2.2 as the primary accessibility standard.
- Reference recommendations should be grounded in trusted W3C sources.