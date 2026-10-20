# Content quality and originality review

The editor's **Save draft & run checks** action saves the current article, then stores an advisory report in the configured database. It is a local editorial aid, not an authorship classifier, legal determination, or publication gate.

## Checks and evidence

- **Originality:** normalized exact paragraphs and five-word-shingle near-overlap against up to 100 recently saved articles and up to 10 reviewer-provided source excerpts. Findings include the matched passage and source link when available. Similarity is a prompt for contextual review, never proof of plagiarism.
- **Writing:** selected stock introductions, filler phrases, and repeated paragraphs.
- **Fact support and citations:** heuristic cues for absolute, time-sensitive, versioned, and quantified claims; linked references are listed with nearby context and URL-format status. The app does not fetch links or independently validate source identity, reachability, relevance, or truth.
- **SEO:** missing or long meta descriptions, long titles, missing or duplicated section headings, and possible overlap with saved article titles. Search intent and ranking are not measured.
- **Technical examples:** unclosed/unlabeled code fences and absent verification cues. Example code is not executed and dependencies are not installed.
- **AI detection:** not run. No detector score is presented and detector output never controls approval.

There is no composite quality score. Reports contain per-finding category, severity, passage, evidence, and a recommended action, plus explicit descriptions of what was not verified. Heuristic matches can be false positives or miss issues; a human editor must inspect source context and claims.
The editor supports a saved meta description and reports descriptive-title/internal-link/topic-overlap hints. Search intent is a human review prompt; the application does not query search results, keyword databases, or live rankings.

## Review and revision flow

1. Save a draft, optionally provide excerpts as one `URL | excerpt` per line, and run the report.
2. Revise in the editor and save. Changed content creates a new revision and makes any previous decision stale.
3. Re-run checks on the saved content. Reports bind to a SHA-256 fingerprint of the exact title and Markdown body.
4. Record **Approve reviewed draft** or **Request changes**. Approval requires an explicit confirmation and a fresh report; it only records a review decision and does not publish.
5. Use the revision history to restore a prior version into the editor, then save it as a new revision.

Existing Blogger draft creation and live-post navigation synchronization remain separate operations with their existing explicit confirmation. No automatic publication is added.

## API and persistence

- `POST /api/articles/{id}/quality-check` accepts up to 10 source excerpts, each capped at 10,000 characters.
- `GET /api/articles/{id}/quality-reports` and `GET /api/articles/{id}/revisions` return saved history.
- `GET /api/articles/{id}/review` returns the current decision state.
- `POST /api/articles/{id}/review` accepts `APPROVED` or `CHANGES_REQUESTED`; approval requires `confirmed: true` and a quality report matching the current article fingerprint.
- Article title, Markdown, and rendered HTML inputs have explicit request-size bounds.

The editor saves the meta description with article revisions and includes it in rendered structured data. Reports retain the supplied excerpt snapshot (up to 1,000 characters per source), source links, and findings. Revisions, reports, and decisions use SQLite tables initialized with the existing application schema. Local SQLite is suitable for local use and tests. On Vercel the default `/tmp` database is ephemeral; these records are not reliable production persistence until a durable store is configured.

All non-public API routes require the single-owner application session on Vercel. Configure `APP_OWNER_PASSWORD` and a unique `APP_SESSION_SECRET` (at least 32 characters). Google OAuth tokens remain server-side; do not add browser storage or client-readable cookies for credentials.
