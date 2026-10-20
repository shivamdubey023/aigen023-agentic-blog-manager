"""Deterministic editorial checks; findings are review prompts, not verdicts."""
from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urlsplit


MAX_REPORT_FINDINGS = 100
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_URL_PATTERN = re.compile(r"(?:https?|ftp|file)://[^\s<>\])}\"']+", re.IGNORECASE)
_MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_GENERIC_OPENINGS = (
    "in today's fast-paced",
    "in today’s fast-paced",
    "in the ever-evolving world",
    "in this article",
    "welcome to",
)
_FILLER_PHRASES = (
    "it is important to note",
    "it's important to note",
    "needless to say",
    "game changer",
    "revolutionary",
    "unlock the power",
    "delve into",
    "in conclusion",
    "seamlessly",
)
_UNSUPPORTED_CLAIM = re.compile(
    r"\b(?:always|never|guarantee[sd]?|proves?|the first|the only|all|every|"
    r"must|cannot|can't|will)\b|\b\d+(?:\.\d+)?\s*(?:%|percent)\b|"
    r"\b(?:in|since)\s+20\d{2}\b|\bversion\s+\d+(?:\.\d+)*\b",
    re.IGNORECASE,
)
_STOP_WORDS = {
    "about", "after", "again", "also", "among", "because", "before", "being",
    "between", "both", "could", "does", "during", "each", "from", "have",
    "into", "more", "most", "other", "over", "same", "should", "some", "such",
    "than", "that", "their", "them", "there", "these", "they", "this", "those",
    "through", "under", "very", "what", "when", "where", "which", "while",
    "with", "would", "your",
}


def content_fingerprint(title: str, markdown: str, meta_description: str = "") -> str:
    canonical = (
        f"{title.strip()}\n{meta_description.strip()}\n{markdown.strip()}"
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _tokens(text: str) -> list[str]:
    return [token.casefold() for token in _TOKEN_PATTERN.findall(text)]


def _normalized(text: str) -> str:
    return " ".join(_tokens(text))


def _plain_text(text: str) -> str:
    text = re.sub(r"(?ms)^```.*?^```[^\n]*(?:\n|$)", " ", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", text)
    text = re.sub(r"(?m)^\s*[-*+]\s+", "", text)
    return re.sub(r"[*_~`>|]", " ", text)


def _paragraphs(text: str) -> list[str]:
    return [
        re.sub(r"\s+", " ", paragraph).strip()
        for paragraph in re.split(r"\n\s*\n", _plain_text(text))
        if len(_tokens(paragraph)) >= 8
    ]


def _shingles(text: str, size: int = 5) -> set[tuple[str, ...]]:
    tokens = _tokens(text)
    if len(tokens) < size:
        return set()
    return {tuple(tokens[index:index + size]) for index in range(len(tokens) - size + 1)}


def _excerpt(text: str, limit: int = 420) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned if len(cleaned) <= limit else cleaned[:limit].rstrip() + "…"


def _finding(
    category: str,
    severity: str,
    title: str,
    excerpt: str,
    evidence: str,
    recommendation: str,
    source_url: str = "",
) -> dict[str, str]:
    finding = {
        "category": category,
        "severity": severity,
        "title": title,
        "excerpt": _excerpt(excerpt),
        "evidence": evidence,
        "recommendation": recommendation,
    }
    if source_url:
        finding["source_url"] = source_url
    return finding


def _citation_contexts(markdown: str) -> dict[str, dict[str, str]]:
    contexts: dict[str, dict[str, str]] = {}
    for paragraph in markdown.split("\n\n"):
        for match in _MARKDOWN_LINK_PATTERN.finditer(paragraph):
            url = match.group(2).strip("<>").rstrip(".,;:")
            try:
                parsed_url = urlsplit(url)
            except ValueError:
                parsed_url = None
            if parsed_url and not parsed_url.scheme and not parsed_url.netloc:
                continue
            contexts.setdefault(url, {
                "context": _excerpt(paragraph, 260),
                "anchor_text": _excerpt(match.group(1), 120),
            })
        for match in _URL_PATTERN.finditer(paragraph):
            url = match.group(0).rstrip(".,;:")
            contexts.setdefault(url, {"context": _excerpt(paragraph, 260), "anchor_text": ""})
    return contexts


def _source_url_status(url: str) -> str:
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            return "invalid"
        return "valid_format" if parsed.scheme == "https" else "http_requires_review"
    except ValueError:
        return "invalid"


def run_quality_review(
    *,
    title: str,
    markdown: str,
    meta_description: str = "",
    primary_keyword: str = "",
    existing_articles: list[dict[str, Any]] | None = None,
    source_material: list[dict[str, str]] | None = None,
    exclude_article_id: int | None = None,
) -> dict[str, Any]:
    """Return bounded editorial findings without fetching URLs or calling paid services."""
    findings: list[dict[str, str]] = []
    articles = existing_articles or []
    sources = source_material or []
    prose_paragraphs = _paragraphs(markdown[:100000])[:100]
    citations = _citation_contexts(markdown)
    cited_normalized = {url.rstrip("/").casefold() for url in citations}

    comparisons: list[dict[str, Any]] = []
    for article in articles:
        if article.get("id") == exclude_article_id:
            continue
        comparisons.append({
            "label": str(article.get("title") or "Saved article"),
            "url": f"/api/articles/{article['id']}" if article.get("id") else "",
            "body": str(article.get("markdown_body") or "")[:50000],
        })
    for source in sources:
        comparisons.append({
            "label": str(source.get("title") or source.get("url") or "Provided source excerpt"),
            "url": str(source.get("url") or ""),
            "body": str(source.get("excerpt") or ""),
        })

    prepared_passages: list[tuple[dict[str, Any], str, set[tuple[str, ...]]]] = []
    exact_sources: dict[str, list[dict[str, Any]]] = {}
    for source in comparisons[:110]:
        for candidate in _paragraphs(source["body"])[:30]:
            candidate_normalized = _normalized(candidate)
            candidate_shingles = _shingles(candidate)
            exact_sources.setdefault(candidate_normalized, []).append(source)
            prepared_passages.append((source,candidate_normalized,candidate_shingles))

    exact_seen: set[tuple[str, str]] = set()
    near_seen: set[tuple[str, str]] = set()
    for paragraph in prose_paragraphs:
        paragraph = paragraph[:5000]
        normalized = _normalized(paragraph)
        if not normalized:
            continue
        matches = exact_sources.get(normalized, []) if len(normalized.split()) >= 8 else []
        if matches:
            for source in matches:
                key = (normalized, source["label"])
                if key in exact_seen:
                    continue
                exact_seen.add(key)
                findings.append(_finding(
                    "originality", "high", "Exact passage match needs review", paragraph,
                    f"This passage exactly matches text in {source['label']!r}. A match is a review signal, not proof of plagiarism.",
                    "Compare the context and provenance, then rewrite or quote and attribute the passage where appropriate.",
                    source["url"],
                ))
        elif len(normalized.split()) >= 20:
            paragraph_shingles = _shingles(paragraph)
            for source, _, candidate_shingles in prepared_passages:
                if not paragraph_shingles or not candidate_shingles:
                    continue
                intersection = len(paragraph_shingles & candidate_shingles)
                similarity = intersection / (len(paragraph_shingles) + len(candidate_shingles) - intersection)
                if similarity < 0.5:
                    continue
                key = (normalized, source["label"])
                if key not in near_seen:
                    near_seen.add(key)
                    findings.append(_finding(
                        "originality", "medium", "Substantial passage overlap needs review", paragraph,
                        f"Five-word shingle overlap is at least 50% against {source['label']!r}. Similarity alone does not establish plagiarism.",
                        "Check whether the shared wording is conventional or attributed; add context and citations or write an original explanation.",
                        source["url"],
                    ))
                break
        if len(findings) >= MAX_REPORT_FINDINGS:
            break

    repeated: set[str] = set()
    for paragraph in prose_paragraphs:
        normalized = _normalized(paragraph)
        if len(normalized.split()) >= 8 and normalized in repeated:
            findings.append(_finding(
                "writing", "medium", "Repeated paragraph", paragraph,
                "The same normalized paragraph appears more than once in this draft.",
                "Remove the duplicate or make each section contribute distinct information.",
            ))
        repeated.add(normalized)

    for phrase in _GENERIC_OPENINGS:
        if markdown.strip().casefold().startswith(phrase):
            findings.append(_finding(
                "writing", "low", "Generic introduction", markdown.strip().split("\n", 1)[0],
                f"The opening uses the stock phrase {phrase!r}.",
                "Start with the reader's concrete problem, a specific result, or the article's scope.",
            ))
            break

    lowered = markdown.casefold()
    filler_hits = [phrase for phrase in _FILLER_PHRASES if phrase in lowered]
    for phrase in filler_hits[:5]:
        match = re.search(re.escape(phrase), markdown, re.IGNORECASE)
        findings.append(_finding(
            "writing", "low", "Filler or promotional phrasing", match.group(0) if match else phrase,
            f"The phrase {phrase!r} can be vague or formulaic in technical guidance.",
            "Replace it with a concrete explanation, limitation, or evidence-backed benefit.",
        ))

    for paragraph in prose_paragraphs:
        if _UNSUPPORTED_CLAIM.search(paragraph) and not _URL_PATTERN.search(paragraph):
            findings.append(_finding(
                "fact-check", "medium", "Important claim has no nearby citation", paragraph,
                "A date, version, quantified, absolute, or predictive claim was detected without a link in the same paragraph. This heuristic does not verify whether the claim is true.",
                "Check the claim against current primary documentation or another reliable source and cite it next to the claim.",
            ))

    seen_citations: set[str] = set()
    citation_report = []
    for url, citation in citations.items():
        context = citation["context"]
        status = _source_url_status(url)
        matched_source = next(
            (
                source for source in sources
                if str(source.get("url") or "").rstrip("/").casefold() == url.rstrip("/").casefold()
            ),
            None,
        )
        relevance = "not_verified"
        if matched_source and matched_source.get("excerpt"):
            source_terms = {term for term in _tokens(matched_source["excerpt"]) if term not in _STOP_WORDS}
            context_terms = {term for term in _tokens(context) if term not in _STOP_WORDS}
            if source_terms and context_terms:
                relevance = "provided_excerpt_text_overlap_signal"
                overlap = len(source_terms & context_terms) / len(source_terms | context_terms)
                if len(source_terms) >= 3 and len(context_terms) >= 3 and overlap < 0.03:
                    findings.append(_finding(
                        "citation", "low", "Citation context may not match provided excerpt", context,
                        f"The cited paragraph has very low token overlap with the excerpt supplied for {url!r}. This compares supplied text only; it does not verify the source page.",
                        "Check that this source supports the nearby claim and that the excerpt is representative.",
                        url,
                    ))
        citation_report.append({
            "url": url,
            "context": context,
            "anchor_text": citation["anchor_text"],
            "format_status": status,
            "reachability": "not_checked",
            "relevance": relevance,
        })
        canonical = url.rstrip("/").casefold()
        if status in {"invalid", "http_requires_review"}:
            findings.append(_finding(
                "citation", "medium" if status == "invalid" else "low",
                "Citation URL needs review", context,
                "The citation is not a valid HTTPS URL." if status == "invalid" else "The citation uses HTTP rather than HTTPS.",
                "Verify the URL and prefer the source's canonical HTTPS address.",
                url,
            ))
        if citation["anchor_text"].strip().casefold() in {"here", "click here", "source", "link"}:
            findings.append(_finding(
                "citation", "low", "Citation attribution is vague", context,
                f"The link label {citation['anchor_text']!r} does not identify the referenced source.",
                "Use a descriptive source or documentation name as the link text.",
                url,
            ))
        if canonical in seen_citations:
            findings.append(_finding(
                "citation", "low", "Duplicate citation URL", context,
                "The same destination is linked more than once in this draft.",
                "Keep the clearest relevant citation and remove redundant links.",
                url,
            ))
        seen_citations.add(canonical)

    for source in sources:
        source_url = str(source.get("url") or "")
        if source_url and _source_url_status(source_url) == "invalid":
            findings.append(_finding(
                "citation", "medium", "Provided source URL is invalid", source_url,
                "The provided source URL is malformed or uses an unsupported scheme.",
                "Supply a complete HTTP or HTTPS source URL; HTTPS is preferred.",
                source_url,
            ))
        elif source_url and source_url.rstrip("/").casefold() not in cited_normalized:
            findings.append(_finding(
                "citation", "low", "Provided source excerpt is not cited", str(source.get("excerpt") or ""),
                "The supplied source material is not linked in the article text.",
                "If the source supports a claim, cite it in the relevant paragraph and verify the attribution.",
                source_url,
            ))

    if not citations:
        findings.append(_finding(
            "citation", "medium", "No linked references found", title,
            "No HTTP(S) links were detected in the draft; source reachability and attribution cannot be reviewed.",
            "Add relevant, checked primary references for material factual and version-specific claims.",
        ))

    if not re.search(r"(?m)^#{2,3}\s+\S", markdown):
        findings.append(_finding(
            "seo", "low", "No H2 or H3 sections found", title,
            "The draft has no Markdown H2/H3 headings.",
            "Organize the article around descriptive sections that match the reader's search intent.",
        ))
    heading_titles = re.findall(r"(?m)^#{2,3}\s+(.+?)\s*#*\s*$", markdown)
    heading_keys = [_normalized(heading) for heading in heading_titles]
    if len(heading_keys) != len(set(heading_keys)):
        findings.append(_finding(
            "seo", "low", "Duplicate section headings", ", ".join(heading_titles),
            "At least two H2/H3 headings normalize to the same text.",
            "Make repeated headings specific to the content in each section.",
        ))
    if len(title.strip()) > 70:
        findings.append(_finding(
            "seo", "low", "Long page title", title,
            f"The title is {len(title.strip())} characters.",
            "Consider a concise title that accurately describes the page; this is an editorial guideline, not a ranking rule.",
        ))
    keyword_terms = set(_tokens(primary_keyword))
    title_terms = set(_tokens(title))
    if keyword_terms and not keyword_terms.issubset(title_terms):
        findings.append(_finding(
            "seo", "low", "Primary topic phrase is absent from the title", title,
            f"The configured topic phrase {primary_keyword.strip()!r} was not found in the title text.",
            "Review whether the title accurately communicates the topic and reader intent; do not force awkward keyword repetition.",
        ))
    description_length = len(meta_description.strip())
    if not description_length:
        findings.append(_finding(
            "seo", "low", "Meta description is missing", title,
            "No explicit meta description is saved for this draft.",
            "Write a concise, accurate summary that reflects the article; do not promise results the content cannot support.",
        ))
    elif description_length > 160:
        findings.append(_finding(
            "seo", "low", "Meta description is long", meta_description,
            f"The saved description is {description_length} characters.",
            "Consider a concise summary. Search snippets can vary and this is not a ranking guarantee.",
        ))

    title_terms = {term for term in _tokens(title) if term not in _STOP_WORDS}
    for article in articles:
        other_title = str(article.get("title") or "")
        other_terms = {term for term in _tokens(other_title) if term not in _STOP_WORDS}
        if article.get("id") == exclude_article_id or not title_terms or not other_terms:
            continue
        overlap = len(title_terms & other_terms) / len(title_terms | other_terms)
        if overlap >= 0.7:
            findings.append(_finding(
                "seo", "low", "Topic may overlap a saved article", title,
                f"The title shares at least 70% of its significant terms with {other_title!r}.",
                "Compare the search intent and coverage; differentiate the topic or consolidate overlapping drafts.",
                f"/api/articles/{article['id']}" if article.get("id") else "",
            ))
            break

    internal_links = []
    for match in _MARKDOWN_LINK_PATTERN.finditer(markdown):
        destination = match.group(2).strip("<>")
        try:
            hostname = urlsplit(destination).hostname
        except ValueError:
            hostname = None
        if destination.startswith("/") or hostname == "aigen023.blogspot.com":
            internal_links.append(destination)
    if len(_tokens(markdown)) >= 300 and not internal_links:
        findings.append(_finding(
            "seo", "low", "No internal links detected", title,
            "No relative or same-site Markdown links were found in this longer draft.",
            "Add relevant internal links when they help readers continue a related task; do not add links solely for a checklist.",
        ))

    code_blocks = re.findall(r"(?ms)^```([^\n]*)\n(.*?)^```[ \t]*$", markdown)
    unclosed_fence = len(re.findall(r"(?m)^```", markdown)) % 2 == 1
    if unclosed_fence:
        findings.append(_finding(
            "technical", "medium", "Unclosed code fence", markdown[-300:],
            "The number of Markdown code-fence markers is odd.",
            "Close the code block and label its language when known.",
        ))
    unlabeled_blocks = sum(not language.strip() for language, _ in code_blocks)
    if unlabeled_blocks:
        findings.append(_finding(
            "technical", "low", "Code block language is unspecified", markdown,
            f"{unlabeled_blocks} fenced code block(s) have no language label.",
            "Add a language identifier such as `python`, `bash`, or `json` where it is clear.",
        ))
    unpinned_installs = []
    for command in re.findall(
        r"(?im)^\s*(?:python\s+-m\s+pip|pip3?)\s+install\s+([^\n#]+)",
        markdown,
    ):
        for package in command.split():
            if package.startswith("-"):
                continue
            if not any(marker in package for marker in ("==", ">=", "<=", "~=", "@")):
                unpinned_installs.append(package.strip(";,"))
    if unpinned_installs:
        package_names = ", ".join(dict.fromkeys(unpinned_installs[:8]))
        findings.append(_finding(
            "technical", "low", "Install examples omit dependency versions", package_names,
            "One or more pip install package names have no version constraint; current compatibility was not checked.",
            "Pin or document tested versions when reproducibility matters, then run the commands in a safe environment.",
        ))
    if code_blocks:
        findings.append(_finding(
            "technical", "info", "Code examples were not executed", "",
            f"{len(code_blocks)} code block(s) were found. This review does not install dependencies or run code.",
            "Test examples in a safe, isolated environment and record relevant dependency versions and expected output.",
        ))
    if not re.search(r"(?i)\b(?:expected output|verify|verification|run the tests|test result)\b", markdown):
        findings.append(_finding(
            "technical", "low", "No verification steps detected", title,
            "No explicit verification or expected-output language was detected; the heuristic may miss equivalent wording.",
            "Include reproducible verification steps and expected output when useful for the article.",
        ))

    findings = findings[:MAX_REPORT_FINDINGS]
    severity_counts = {
        severity: sum(1 for item in findings if item["severity"] == severity)
        for severity in ("high", "medium", "low", "info")
    }
    return {
        "findings": findings,
        "finding_counts": severity_counts,
        "citations": citation_report,
        "source_material_reviewed": [
            {
                "url": str(source.get("url") or ""),
                "title": str(source.get("title") or ""),
                "excerpt": _excerpt(str(source.get("excerpt") or ""), 1000),
            }
            for source in sources
        ],
        "checks": {
            "originality_corpus": "saved local articles and reviewer-provided excerpts",
            "citation_reachability": "not_checked",
            "citation_relevance": "provided-excerpt text overlap only; source page not verified",
            "fact_accuracy": "not_verified",
            "code_execution": "not_run",
            "dependency_versions": "not_resolved_or_installed",
            "ai_detection": "not_run",
            "automated_plagiarism_verdict": "never_provided",
            "search_intent": "human review required; no search results or keyword database queried",
        },
        "human_review_prompts": [
            "Confirm the article answers the intended reader question and is distinct from existing topics.",
            "Verify important claims against current, reliable primary sources.",
            "Confirm examples, dependencies, and outputs in an isolated environment before publishing.",
        ],
        "limitations": [
            "Similarity findings identify passages for human review; they do not prove plagiarism.",
            "Facts, source-page relevance, and URL reachability are not independently verified or fetched; provided excerpt overlap is only a text signal.",
            "Code is not executed, dependencies are not installed, and AI authorship is not assessed.",
            "Results are editorial prompts, not a compliance guarantee or a single quality score.",
        ],
    }
