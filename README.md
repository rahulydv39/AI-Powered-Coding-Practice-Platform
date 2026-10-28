# AI Coding Interview Gym

AI Coding Interview Gym is a dedicated practice platform designed to prepare software engineering students for modern, AI-assisted technical interviews.

---

## 1. Prerequisites

Before running the project locally on macOS, ensure you have the following installed:

- **Node.js**: v18.18+ (tested with v26)
- **pnpm**: v9+ or v12+ (`npm install -g pnpm`)
- **Python**: v3.12+ (tested with Python 3.12.14)
- **Docker Desktop or OrbStack** *(Required for isolated Python code execution and PostgreSQL)*
- **AI Model Provider Keys** *(Optional: Google Gemini, Anthropic Claude, or OpenAI)*

---

## 2. Quick Start Guide

### Step 1: Configure Environment Variables & Start Database

From the repository root:

```bash
cp .env.example .env
```

Start the local PostgreSQL 16 container:
```bash
docker compose -f infra/docker-compose.yml up -d
```

To configure AI provider assistance, edit `.env` and configure your preferred provider(s):

```bash
# Multi-Provider AI Assistant Configuration (Phase 3 & Phase 5.1)
AI_ASSISTANT_ENABLED=true
AI_DEFAULT_PROVIDER=gemini
AI_RATE_LIMIT_PER_MINUTE=10

# Google Gemini (https://aistudio.google.com/)
GEMINI_API_KEY="your-gemini-api-key"
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT_SECONDS=15.0

# Anthropic Claude (https://console.anthropic.com/)
ANTHROPIC_API_KEY="your-anthropic-api-key"
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_TIMEOUT_SECONDS=15.0

# OpenAI (https://platform.openai.com/)
OPENAI_API_KEY="your-openai-api-key"
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=15.0
```

> [!NOTE]
> If all AI keys are left blank, the application still works completely. The deterministic Docker test runner, submission evaluation, PostgreSQL scoring database, progress analytics, and deterministic solution review are completely unaffected. The AI panel displays a clear actionable message if the chosen provider's key is missing.

---

### Step 2: Apply Database Migrations & Start FastAPI Backend

1. Navigate to the API application:
   ```bash
   cd apps/api
   ```

2. Create and activate a Python 3.12 virtual environment:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```

4. Apply Alembic migrations to create tables and indexes:
   ```bash
   alembic upgrade head
   ```

5. Run the automated test suite (101 tests):
   ```bash
   pytest -v
   ```

6. Start the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will now be accessible at `http://localhost:8000`.

---

### Step 3: Start the Next.js Frontend

1. Open a new terminal window and navigate to the web application:
   ```bash
   cd apps/web
   ```

2. Install dependencies:
   ```bash
   pnpm install
   ```

3. Build the production bundle to verify types:
   ```bash
   pnpm build
   ```

4. Start the development server:
   ```bash
   pnpm dev
   ```

The frontend will now be running at `http://localhost:3000`.

---

### Step 4: Open the Challenge Workspace

Navigate to:
**`http://localhost:3000/challenges/request-deduplication`**

---

## 3. Platform Capabilities & Workflows

### 1. Request Deduplication Debugging Challenge
- **Problem**: In distributed web services, duplicate requests cause race conditions. Fix the Python function to filter duplicates:
  ```python
  def process_request(request_id: str, seen_ids: set[str]) -> bool:
      ...
  ```
- **Requirements**:
  1. First occurrence returns `True` and is registered in `seen_ids`.
  2. Subsequent occurrences return `False`.
  3. Different IDs are evaluated independently.
  4. Empty string or non-string inputs raise `ValueError`.
- **Reset Code**: Restores the original starter code.

### 2. Exploratory "Run Tests" vs Formal "Submit Solution"
- **Run Tests (Exploratory Attempt)**:
  * Runs code inside an isolated ephemeral Docker container (`--network none`, read-only filesystem, non-root user).
  * Returns detailed per-test pass/fail status and assertion failure messages.
  * Allows unlimited exploratory iterations without recording a permanent submission.
- **Submit Solution (Formal Submission & Deterministic Scoring)**:
  * Evaluates code against authoritative hidden server-side test harness.
  * Computes deterministic correctness score:
    $$\text{score} = \operatorname{round}\left(\frac{\text{passed\_tests}}{\text{total\_tests}} \times 100\right)$$
  * Persists candidate attempt, status, score, execution time, and rubric version (`correctness-v1`) to the PostgreSQL `submissions` table.
  * Displays formal evaluation panel with score gauge, pass/fail progress bar, submission ID, and required disclaimer:
    > *"Correctness score measures test performance; it does not yet measure reasoning or code quality."*
  * **Infrastructure Safety**: If Docker is unavailable, submissions fail safely without penalizing the candidate with a 0 score.

### 3. Post-Submission Solution Review & Learning Experience
After a completed formal submission, clicking **"Review Solution"** opens the comprehensive learning review:
- **Reference Implementation**: Displays the complete authoritative solution (`solution_reference.py`) with copy helper. Your active editor code remains completely preserved and untouched.
- **Key Implementation Decisions**: Detailed breakdowns of the 4 core architectural choices:
  1. *Fail-Fast Input Validation*: Why invalid inputs raise `ValueError` rather than silently returning `False`.
  2. *Pre-Mutation Membership Check*: Why `request_id in seen_ids` must precede state registration.
  3. *State Registration*: Why `seen_ids.add(request_id)` must update the session set.
  4. *Boolean Return Contract*: Why explicit `True` (first arrival) and `False` (duplicate) gating matters.
- **Submission Comparison & Line Diff**:
  * Semantic categorization: *Exact Match*, *Formatting Difference Only*, *Alternative Correct*, *Functional Bug*, or *Syntax Error*.
  * Formatting or docstring differences are never falsely labeled as mistakes.
  * Expandable line-by-line unified diff showing additions (`+`) and removals (`-`).
- **Architectural Takeaways**: Deep dives into idempotency, hash table $O(1)$ set complexity, defensive programming, and scaling to distributed Redis sets with TTL.
- **Multi-Provider AI Review**: On-demand AI comparison analyzing nuances of your specific attempt with Gemini, Claude, or OpenAI.

### 4. Multi-Provider AI Assistant (Backend-Only Architecture)
Located in the challenge practice workspace and solution review panels:
- **Supported Providers**:
  * **Google Gemini** (`gemini-2.5-flash`) via `google-genai` SDK.
  * **Anthropic Claude** (`claude-3-5-sonnet-20241022`) via `anthropic` SDK.
  * **OpenAI** (`gpt-4o-mini`) via `openai` SDK.
- **Provider Selector**:
  * Seamlessly toggle between Gemini, Claude, and OpenAI directly in the UI.
  * Accessible, keyboard-operable, dark UI dropdown indicating provider status (`Ready` vs `Key Needed`).
  * Selection is persisted in `localStorage` browser preference only. **API keys and secrets are never stored in browser storage.**
- **No Silent Fallback**:
  * If a selected provider's key is unconfigured, rate-limited, or times out, the system returns a safe, descriptive error message without silently falling back to another provider, allowing the student to explicitly switch providers.
- **"Explain Code"**:
  * Analyzes the current editor code in plain, beginner-friendly language.
  * Breaks down inputs, control flow, state changes, and edge cases.
- **"Get Hint" (Progressive Debugging Policy)**:
  * **Level 1**: Points toward the high-level concept or requirement.
  * **Level 2**: Narrows down to the specific condition or state tracking missing.
  * **Level 3**: Provides concrete debugging guidance without dumping a full solution.
- **Security & Sandbox Isolation**:
  * Untrusted student code is isolated with `<student_code>` delimiters.
  * AI providers never evaluate or modify deterministic correctness scores.
  * API keys and raw error traces are strictly kept on the backend and never leaked to responses or client logs.

### 5. Student Progress & Submission History (Phase 5.1 & Phase 5.2)
Accessible from the global navigation at `http://localhost:3000/progress`:
- **Progress Summary Analytics**:
  * **Total Formal Submissions**: All completed `Submit Solution` evaluations belonging to the authenticated student.
  * **Distinct Challenges Attempted**: Unique challenge count for the student.
  * **Best Correctness Score**: Highest score achieved across the student's scorable attempts.
  * **Most Recent Score**: Score of the student's newest scorable submission.
  * **Average Correctness Score**: Mean score across the student's scorable attempts (calculated as $\text{round}(\frac{\sum \text{score}}{N}, 1)$).
  * **Test Assertions**: Cumulative passed vs. failed test assertions for the student.
  * **Per-Challenge Metrics**: Distinct attempt counts, best score, and latest score per challenge.
  * **Progress Over Time**: Interactive chronological score timeline graph.
- **Calculation Semantics for Unscorable Runs**:
  * Infrastructure failures (e.g. `runner_unavailable` where Docker was offline) are retained in submission history and counted toward total formal submissions.
  * Unscorable runs are **strictly excluded** from score aggregates (`best_score`, `most_recent_score`, and `average_score`).
  * An unscorable attempt is **never counted as a zero score**.
  * Handled cleanly with an empty database or fresh student account without division by zero.
- **Submission History Table**:
  * Newest submissions displayed first with stable tie-breaking (`ORDER BY created_at DESC, id DESC`).
  * Challenge title and unique submission ID.
  * Timestamp formatted in the student's **local browser time**.
  * Correctness score badge (100% emerald, partial amber, 0% red, or "Unscorable").
  * Test counts (passed / total).
  * Execution status and container duration.
  * **Historical Review Action**: Clicking "Review" opens that specific historical submission's authoritative review, evaluating the exact code snapshot submitted for that attempt rather than current editor contents.
  * **Code Snapshot Viewer**: Inspect the exact Python code evaluated for each historical submission.
  * Pagination with configurable page sizes (default 15 per page).

### 6. Custom Authentication & Isolated Student Dashboard (Phase 5.2)
- **Zero Dummy Data**: The student dashboard renders only real, persisted, user-scoped metrics. Placeholder KPIs and fabricated data have been completely removed. New students with zero submissions see a clean, encouraging empty state prompting them to start their first challenge.
- **Data Isolation**: All submission records are assigned a `user_id`. Queries for progress summary, challenge breakdowns, score timeline graphs, submission history, snapshots, and solution reviews are strictly filtered by `current_user.id`. Legacy unassigned submissions (`user_id = NULL`) remain safely isolated from student dashboards and review endpoints.
- **Custom Dark-Themed Auth Pages**:
  * `/login`: Sign in with email and password or social providers, password visibility toggle, generic non-leaking error responses, accessible focus states.
  * `/signup`: Registration with full name, email, password confirmation, client- and server-side validation.
  * `/forgot-password`: Single-use expiring password recovery request.
  * `/reset-password`: Token-based password reset without leaking secrets in logs.
  * `/account`: Student profile information, linked OAuth providers, and LeetCode external profile status.
- **Secure Server-Managed Sessions**:
  * Passwords hashed using Argon2id (`argon2-cffi`). Plaintext passwords and password hashes are never returned to clients or logged.
  * Server-side session tracking in PostgreSQL `user_sessions` with cryptographically random 32-byte tokens hashed with SHA-256 in the database.
  * Session cookie: `HttpOnly`, `SameSite=Lax`, `Secure` (in production), 7-day expiration (`max_age=604800`).
  * CSRF defense via `SameSite=Lax` cookies and custom `X-Gym-CSRF: 1` header on state-changing requests.
  * Revocation support on sign out (`/api/v1/auth/logout`) and session expiration.
- **Social OAuth Sign-In (Google, GitHub, Apple)**:
  * Google OAuth with PKCE flow (`code_challenge` / `code_verifier`).
  * GitHub OAuth and Apple Sign-In support.
  * Ephemeral signed cookies for OAuth state verification (`oauth_state`, `oauth_verifier`) preventing CSRF and login injection.
  * Account linking in `user_oauth_accounts` mapping external provider identities (`sub` / `id`) to existing or newly created user accounts without account hijacking.
  * Clear UI notices when an OAuth provider's credentials are not yet configured in local development.
- **LeetCode Clarification**:
  * LeetCode does not support an official public third-party OAuth 2.0 / OIDC provider.
  * Documented explicitly in `/api/v1/auth/leetcode/status` and on the Account settings page.
  * Treated strictly as optional external profile linking, never as an authentication mechanism.

---

## 4. Local URLs and Available Endpoints

| Service / Endpoint | Method | URL | Description |
| :--- | :--- | :--- | :--- |
| **Student Sign In** | GET | `http://localhost:3000/login` | Email/password & social sign-in page |
| **Student Registration** | GET | `http://localhost:3000/signup` | Account creation page with password confirmation |
| **Forgot Password** | GET | `http://localhost:3000/forgot-password` | Password recovery request page |
| **Reset Password** | GET | `http://localhost:3000/reset-password` | Single-use token password reset page |
| **Account Profile** | GET | `http://localhost:3000/account` | Protected student profile & linked OAuth accounts |
| **Progress & History Dashboard** | GET | `http://localhost:3000/progress` | User-scoped progress analytics, KPI cards, timeline, & submission history |
| **Frontend Challenge Page** | GET | `http://localhost:3000/challenges/request-deduplication` | Challenge workspace with code editor, submission action & AI selector |
| **API Register** | POST | `http://localhost:8000/api/v1/auth/register` | Create account with Argon2id password hash |
| **API Login** | POST | `http://localhost:8000/api/v1/auth/login` | Authenticate & issue HttpOnly session cookie |
| **API Logout** | POST | `http://localhost:8000/api/v1/auth/logout` | Revoke session & clear session cookie |
| **API Current User** | GET | `http://localhost:8000/api/v1/auth/me` | Fetch authenticated student profile |
| **API Forgot Password** | POST | `http://localhost:8000/api/v1/auth/forgot-password` | Request password reset token |
| **API Reset Password** | POST | `http://localhost:8000/api/v1/auth/reset-password` | Set new password with valid token |
| **API OAuth Providers** | GET | `http://localhost:8000/api/v1/auth/providers` | Check status of Google, GitHub, Apple OAuth configs |
| **API LeetCode Status** | GET | `http://localhost:8000/api/v1/auth/leetcode/status` | Clarification on LeetCode profile linking vs OAuth |
| **API Progress Summary** | GET | `http://localhost:8000/api/v1/progress/summary` | User-scoped progress statistics and per-challenge metrics |
| **API Submission History** | GET | `http://localhost:8000/api/v1/progress/history` | Paginated formal submission records for current user |
| **API Submission Snapshot** | GET | `http://localhost:8000/api/v1/progress/submissions/{id}` | User-scoped historical submission details & source code snapshot |
| **API AI Providers List** | GET | `http://localhost:8000/api/v1/challenges/ai/providers` | List supported AI providers (Gemini, Claude, OpenAI) & configuration status |
| **API Challenge Metadata** | GET | `http://localhost:8000/api/v1/challenges/request-deduplication` | Challenge statement, starter code, test summaries (no reference solution) |
| **API Code Runner** | POST | `http://localhost:8000/api/v1/challenges/request-deduplication/run` | Exploratory execution in isolated container sandbox |
| **API Solution Submission** | POST | `http://localhost:8000/api/v1/challenges/request-deduplication/submit` | Authenticated formal grading, deterministic scoring, PostgreSQL persistence |
| **API Solution Review** | GET | `http://localhost:8000/api/v1/challenges/request-deduplication/submissions/{id}/review` | Authenticated post-submission review with line diff & multi-provider AI |
| **AI Explain Code** | POST | `http://localhost:8000/api/v1/challenges/request-deduplication/ai/explain` | Explain student code via selected AI provider (`gemini`, `claude`, `openai`) |
| **AI Progressive Hint** | POST | `http://localhost:8000/api/v1/challenges/request-deduplication/ai/hint` | Request progressive hints via selected AI provider |
| **API Health (Root)** | GET | `http://localhost:8000/health` | Lightweight ping (`{"status": "ok"}`) |
| **API Diagnostic Health** | GET | `http://localhost:8000/api/v1/health` | Detailed status (`version`, `database`, `environment`) |
| **Interactive API Docs** | GET | `http://localhost:8000/docs` | Swagger UI documentation |

---

## 5. Security & Solution Access Rules

### Data Isolation & Access Control (Phase 5.2)
- **User Ownership of Submissions**: Every formal submission is tied to the authenticated user's ID (`user_id = current_user.id`).
- **Student Data Boundaries**: Progress summary, challenge breakdowns, score timeline graphs, submission history, snapshots, and solution reviews are strictly isolated to the caller's session. Attempting to query another student's submission ID returns an immediate 404 Not Found error.
- **Unassigned Legacy Submissions**: Submissions created prior to Phase 5.2 have `user_id = NULL`. These historical records are retained in PostgreSQL for audit purposes but are never returned in any student's private history or progress calculations.
- **Post-Submission Only Review**: The reference solution and solution review cannot be accessed before completing a formal submission. Pre-submission metadata and exploratory run endpoints never expose the reference implementation.
- **Database Validation**: The review endpoint requires a valid `submission_id` from the PostgreSQL `submissions` table. It verifies that the record belongs to the requested challenge, belongs to `current_user.id`, and has a completed, scorable status (`score is not None` and `status != 'runner_unavailable'`).
- **Data Integrity**: Requesting a review uses the code stored in the database for that submission ID, not arbitrary client parameters. Opening a review never alters the recorded score, test counts, status, or timestamps, and does not create duplicate database records.
- **Sandbox Non-Negotiables**: Code execution happens strictly inside isolated Docker containers with no host execution fallback.
- **Deterministic Truth**: Deterministic pytest tests remain the sole source of truth for correctness scores. AI models never grade code or alter scores.

---

## 6. Verification Commands

### Automated Backend Test Suite (Pytest)
```bash
cd apps/api
source .venv/bin/activate
pytest -v
```
*Executes 101 automated tests covering:*
- **Authentication & Sessions (`test_auth.py`, `test_auth_security_hardening.py`)**:
  * Registration success and password hashing with Argon2id.
  * Duplicate email rejection (normalized lowercase).
  * Validation rejection on invalid email formats, weak passwords, and missing fields.
  * Login success, session creation, and secure cookie issuance (`HttpOnly`, `SameSite=Lax`, `Path=/`).
  * Expired session rejection (HTTP 401).
  * CSRF protection verification on state-changing requests (rejection of cross-origin/form-urlencoded payloads without headers).
  * Generic non-enumerating error messages on invalid email or wrong password.
  * Single-use password reset token lifecycle and expiration.
  * OAuth pre-account hijacking prevention for existing password-protected accounts.
  * CORS preflight and credentials handling (`Access-Control-Allow-Credentials: true`).
- **Data Isolation & Security Boundaries (`test_data_isolation.py`)**:
  * Complete boundary separation: User A and User B cannot see each other's submissions, progress metrics, snapshots, or solution reviews.
  * Unauthenticated requests to protected endpoints return 401 Unauthorized.
  * Pre-auth unassigned submissions (`user_id = NULL`) cannot be accessed by any user.
- **Social OAuth & Provider Verification (`test_oauth.py`)**:
  * Provider listing and configuration status detection.
  * Descriptive error responses when unconfigured OAuth providers are accessed.
  * Google OAuth PKCE authorization and session creation callback.
  * GitHub OAuth callback and account linking in `user_oauth_accounts`.
  * OAuth state verification and CSRF rejection on state mismatches.
  * LeetCode status endpoint verifying unsupported OAuth clarification.
- **Student Progress & Submission History (`test_progress.py`)**:
  * Empty user account edge case (zero counts, null aggregates, no division by zero).
  * Single and multiple attempts on the same challenge scoped to `user_id`.
  * Multiple distinct challenges.
  * Correct best, latest, and average score calculations.
  * Unscorable runs (`runner_unavailable` / `score=None`) excluded from score aggregates without counting as 0.
  * Pagination, page size bounds, and stable sorting (`created_at DESC, id DESC`).
  * Exploratory runs never generate formal submission history records.
  * Preserved code snapshot retrieval for historical attempts.
- **Multi-Provider AI Architecture (`test_multi_provider_ai.py`)**:
  * Provider allowlist validation (`gemini`, `claude`, `openai`).
  * Rejection of unsupported providers with HTTP 400 Bad Request.
  * No silent fallback: explicit configuration errors when chosen provider key is missing.
  * Claude and OpenAI adapters error mapping (auth, quota/rate-limits, timeouts, API errors).
  * AI endpoints (`explain`, `hint`, `review`) respecting selected provider.
  * Secrecy: API keys never exposed in responses or logs.
- **Scoring & Solution Access Integrity (`test_submission.py`, `test_solution_review.py`)**:
  * Post-submission solution review endpoint access controls (404 on missing/unowned IDs, 400 on non-scorable attempts).
  * Historical review targets specific historical submission and uses historical submitted code.
  * Reference solution secrecy in challenge metadata and exploratory run responses.
  * Semantic diff categorization (identical, formatting only, alternative correct, functional bugs, syntax errors).

### Frontend Lint, TypeScript Check, & Production Build
```bash
cd apps/web
pnpm run lint
pnpm run build
```
*Compiles the Next.js App Router (Turbopack) and verifies strict TypeScript types with zero errors across all 9 routes (`/`, `/account`, `/challenges/request-deduplication`, `/forgot-password`, `/login`, `/progress`, `/reset-password`, `/signup`, `/_not-found`).*

---

## 7. How to Test the Complete Flow Locally

### Testing Authentication & Account Creation
1. Start PostgreSQL (`docker compose -f infra/docker-compose.yml up -d`), FastAPI (`uvicorn app.main:app --port 8000`), and Next.js (`pnpm dev`).
2. Navigate to `http://localhost:3000/signup`.
3. Register a new student account (e.g. `student@gym.test`, password `Password123!`).
4. Upon successful registration, you are redirected to `/progress`.
5. Observe the welcome empty state: **"Welcome to your Student Dashboard"**, with 0 submissions and an invitation to complete your first challenge.
6. Check the top navigation: notice your user email and the account dropdown with **Profile Settings** and **Sign Out**.
7. Navigate to `/account` to view your profile details, linked OAuth providers, and the LeetCode profile linking explanation.

### Testing Data Isolation Between Students
1. Navigate to `http://localhost:3000/challenges/request-deduplication`.
2. Submit a solution to record a formal submission for `student@gym.test`.
3. Return to `http://localhost:3000/progress` and verify your submission appears in the KPI cards and submission history.
4. Click **Sign Out** from the user dropdown.
5. Create a second account (e.g. `student2@gym.test`) at `/signup`.
6. Visit `http://localhost:3000/progress`: observe that the dashboard shows 0 submissions and the first student's submissions and metrics are completely hidden.
7. Attempt to directly request the first student's submission review via API: verify that the backend responds with HTTP 404 Not Found.

### Testing Multi-Provider AI Selector
1. Navigate to `http://localhost:3000/challenges/request-deduplication`.
2. Locate the **AI Model Provider** selector in the AI Coach panel header.
3. Select **Google Gemini**:
   - Click **Explain Code** or **Get Hint**. Feedback is generated and labelled with `GEMINI` and the model name (`gemini-2.5-flash`).
4. Select **Anthropic Claude** or **OpenAI**:
   - If an API key is configured in `apps/api/.env`, the request executes with Claude/OpenAI and displays the corresponding provider tag.
   - If the API key is not configured, the assistant displays an informative actionable error banner explaining that the key is missing, without silently falling back to Gemini, and offering a one-click button to switch to Gemini.
5. Submit a solution, click **Review Solution**, and test the AI Mentor Review with the chosen provider selector in Section E.
6. Verify that your selection persists across page reloads via `localStorage`.
   - Section C updates to reflect `Exact Match` / `Functionally Correct` without falsely inventing mistakes.
