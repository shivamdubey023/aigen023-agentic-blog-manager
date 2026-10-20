# Development rules

These rules describe the current FastAPI, vanilla-JavaScript, and Vercel project. Preserve the existing API and integrations unless a documented change is required.

## Architecture and changes

- Keep the request flow browser → same-origin FastAPI route → existing service/integration or repository. Do not put business logic in browser code or duplicate the existing Python adapters.
- Use `api/index.py` for HTTP routing and validation, `core/` for shared application logic and persistence, and `property_a_blog/` for Blogger, SEO, and publication behavior.
- Keep the frontend dependency-free unless a real feature requires an additional library. There is no frontend build step.
- Do not run Streamlit as the Vercel application. `app.py` is legacy UI; migrate and verify its remaining queue, export, analytics, and settings behaviors before removing it or claiming the migration is complete.
- Treat SQLite under Vercel `/tmp` as temporary. Do not describe it as durable production storage or migrate data without approval.
- Quality reviews must present evidence and actionable findings, not a single score. Similarity is a human-review signal, never a plagiarism verdict; approval does not publish.

## Backend and API

- Define and validate request bodies with Pydantic models. Validate lengths, identifiers, status values, and external URLs at the boundary; parameterize SQL values.
- Preserve response formats where practical. Use meaningful HTTP status codes and FastAPI `HTTPException` for expected client errors.
- Do not return tracebacks, provider responses containing secrets, access tokens, or raw internal exception details to clients. Log only useful, redacted diagnostics.
- Keep credentials server-side. Never put AI keys or Google OAuth tokens in HTML, JavaScript, URLs, browser storage, or client-readable cookies.
- The application has no built-in owner login or API authorization. Before production deployment, require platform-level access protection (such as Vercel Deployment Protection) for the UI and all API routes. Do not publish a publicly accessible deployment containing private drafts or live integration credentials.
- Keep Google OAuth tokens server-side. Do not add Google token headers, browser storage, or client-readable token cookies.
- The frontend uses same-origin requests and does not enable CORS. Do not add broad cross-origin credential access.
- Require explicit confirmation before creating Blogger drafts or changing live post HTML. Avoid blind publish retries and preserve existing content.
- Do not make unapproved, destructive database changes or introduce a paid storage service.

## Frontend, accessibility, and privacy

- Use semantic HTML, associated labels, keyboard-operable controls, visible focus indicators, and responsive layouts. Check phone-width layouts for clipped content and horizontal overflow.
- Use `textContent` for plain text. Escape untrusted values before HTML insertion, validate URL schemes before making links, and include `rel="noopener noreferrer"` on links opened in a new tab.
- Render genuine loading, empty, failure, and success states. Do not fabricate analytics, integration health, or successful actions.
- Keep browser requests same-origin and use server APIs for privileged operations. Never trust browser-supplied identity or role data.
- Avoid storing integration credentials in `localStorage`, page markup, or client-readable cookies. Do not log OAuth codes, cookies, or API keys.

## Integrations and failures

- Mock AI, Google, Blogger, image providers, and network calls in unit tests. Routine checks must not require paid credentials or publish to a live site.
- Keep quality-review tests offline with isolated SQLite files. Do not fetch citation URLs, run article code, call AI detectors, or label similarity as proof of plagiarism.
- A review decision must reference a fresh report for the exact saved draft. Any edit invalidates the earlier decision; publishing and live Blogger edits stay separate, explicitly confirmed actions.
- Preserve provider selection; do not silently fall back to a different model or service.
- Set finite timeouts on outbound requests and handle provider failures explicitly. Do not turn an error into a success-shaped response.
- Keep Search Console metrics tied to actual API responses and clearly identify unavailable data. AdSense reporting is not implemented.

## Dependencies and configuration

- Reuse the existing Python and browser platform before adding dependencies. Explain new runtime or test-only dependencies in the relevant manifest and documentation.
- Use `requirements.txt` for application dependencies and `requirements-dev.txt` for test-only tools.
- Store local secrets in ignored `.env` files and deployment secrets in Vercel project settings. Keep placeholder-only examples free of actual credentials.
- Document environment variable names and purpose, never secret values. Review diffs for accidental secret or local database additions.
- Do not alter `.github/copilot-instructions.md` or add, rename, or delete Copilot instruction files.

## Tests and CI

- Add a regression test for behavior changes, especially API status codes, validation, persistence, OAuth errors, authorization, HTML escaping, and external URL handling.
- Use isolated temporary SQLite paths and restore patched environment or module state in test cleanup.
- Run the relevant unit tests and Python compilation before merging. Check all browser JavaScript files with `node --check`.
- GitHub Actions must use read-only repository permissions, preserve the `main` and `refactor/**` push and `main` pull-request triggers, and fail when required checks fail.
- Do not add duplicate workflow files for checks already covered by `validate.yml`. There is no version-release automation or frontend bundle build configured.
- Do not claim a check passed if it was not run. If a local runtime is unavailable, report the limitation and rely on CI only after it has actually completed.

## Git and deployment safety

- Keep a change focused. Inspect the working tree and preserve unrelated user changes; never overwrite local secrets or databases.
- Review `git diff --check` and the complete intended diff before merging. Never commit secrets, generated credentials, or private production data.
- Validate `vercel.json` routing when changing the root page, static assets, eBook PWA, or API paths. Test `/`, `/static/...`, `/api/health`, and an unknown API path after a deployment.
- Verify Vercel environment variables and the exact Google OAuth callback URL before enabling integrations. Do not claim a deployment is verified without deploying and testing it.
- Remember Vercel function instances are ephemeral: no in-process queue worker, SQLite durability, or shared module-global session state is guaranteed.

## Pre-commit checklist

- [ ] Change is focused; unrelated working-tree files are preserved.
- [ ] Inputs and URLs are validated; untrusted frontend values are escaped.
- [ ] Findings disclose evidence and verification limits; stale approvals cannot be reused.
- [ ] Secrets and generated/local data are absent from the diff.
- [ ] Relevant tests and compile checks ran, or the unavailable check is clearly reported.
- [ ] `git diff --check` is clean and docs match actual behavior.

## Pre-deployment checklist

- [ ] CI passes on the intended branch.
- [ ] Vercel routes serve the web app and assets and return correct API status codes.
- [ ] Required environment variables and OAuth callback are configured privately.
- [ ] Platform-level access protection covers the UI and every API route before production exposure; OAuth tokens remain server-side.
- [ ] Persistent storage requirements are met; do not rely on Vercel `/tmp` for production records.
- [ ] Blogger publishing and live updates remain explicit, confirmed actions.