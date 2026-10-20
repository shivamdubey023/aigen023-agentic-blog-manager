"""Core persistence and application services."""
from __future__ import annotations
import json, os, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from core.content_quality import content_fingerprint

APP_ROOT = Path(__file__).resolve().parents[1]

def _default_db_path() -> Path:
    if "CONTENT_OPS_DB" in os.environ:
        return Path(os.environ["CONTENT_OPS_DB"])
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return Path("/tmp/content_ops.db")
    return APP_ROOT / "content_ops.db"

DB_PATH = _default_db_path()

def get_db_path() -> Path:
    if "CONTENT_OPS_DB" in os.environ:
        return Path(os.environ["CONTENT_OPS_DB"])
    return DB_PATH

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    path = get_db_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        path = Path("/tmp/content_ops.db")
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=15, isolation_level="DEFERRED")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 15000")
    try:
        try: conn.execute("PRAGMA journal_mode = WAL")
        except sqlite3.DatabaseError: pass
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db() -> None:
    with connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS articles (
          id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT NOT NULL DEFAULT '',
          primary_keyword TEXT NOT NULL DEFAULT '', title TEXT NOT NULL DEFAULT '',
          meta_description TEXT NOT NULL DEFAULT '',
          markdown_body TEXT NOT NULL DEFAULT '', rendered_html TEXT NOT NULL DEFAULT '',
          schema_json TEXT NOT NULL DEFAULT '{}',
          status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(status IN ('QUEUED','DRAFT','PAUSED','PUBLISHED')),
          blogger_post_id TEXT NOT NULL DEFAULT '', blogger_blog_id TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL, published_at TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
        CREATE INDEX IF NOT EXISTS idx_articles_updated ON articles(updated_at DESC);
        CREATE TABLE IF NOT EXISTS article_revisions (
          id INTEGER PRIMARY KEY AUTOINCREMENT, article_id INTEGER NOT NULL,
          revision_number INTEGER NOT NULL, title TEXT NOT NULL,
          meta_description TEXT NOT NULL DEFAULT '', markdown_body TEXT NOT NULL,
          rendered_html TEXT NOT NULL DEFAULT '',
          reason TEXT NOT NULL DEFAULT 'saved', created_at TEXT NOT NULL,
          FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE,
          UNIQUE(article_id, revision_number)
        );
        CREATE INDEX IF NOT EXISTS idx_article_revisions_article
          ON article_revisions(article_id, revision_number DESC);
        CREATE TABLE IF NOT EXISTS quality_reports (
          id INTEGER PRIMARY KEY AUTOINCREMENT, article_id INTEGER NOT NULL,
          content_hash TEXT NOT NULL, report_json TEXT NOT NULL, created_at TEXT NOT NULL,
          FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_quality_reports_article
          ON quality_reports(article_id, id DESC);
        CREATE TABLE IF NOT EXISTS review_decisions (
          id INTEGER PRIMARY KEY AUTOINCREMENT, article_id INTEGER NOT NULL,
          content_hash TEXT NOT NULL,
          decision TEXT NOT NULL CHECK(decision IN ('APPROVED','CHANGES_REQUESTED')),
          notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
          FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_review_decisions_article
          ON review_decisions(article_id, id DESC);
        CREATE TABLE IF NOT EXISTS automation_queue (
          id INTEGER PRIMARY KEY AUTOINCREMENT, article_id INTEGER,
          state TEXT NOT NULL DEFAULT 'PAUSED' CHECK(state IN ('RUNNING','PAUSED')),
          retry_count INTEGER NOT NULL DEFAULT 0, max_retries INTEGER NOT NULL DEFAULT 3,
          execution_log TEXT NOT NULL DEFAULT '[]', updated_at TEXT NOT NULL,
          FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS affiliate_vault (
          id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT NOT NULL,
          trigger_keywords TEXT NOT NULL DEFAULT '[]', tracking_url TEXT NOT NULL,
          disclosure_snippet TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS oauth_states (
          state TEXT PRIMARY KEY, created_at TEXT NOT NULL, code_verifier TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS system_credentials (
          key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_products (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          url TEXT NOT NULL,
          price TEXT NOT NULL DEFAULT '',
          description TEXT NOT NULL DEFAULT '',
          badge TEXT NOT NULL DEFAULT 'Recommended Guide',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        """)
        article_columns = {row["name"] for row in conn.execute("PRAGMA table_info(articles)").fetchall()}
        if "meta_description" not in article_columns:
            conn.execute("ALTER TABLE articles ADD COLUMN meta_description TEXT NOT NULL DEFAULT ''")
        revision_columns = {row["name"] for row in conn.execute("PRAGMA table_info(article_revisions)").fetchall()}
        if "meta_description" not in revision_columns:
            conn.execute("ALTER TABLE article_revisions ADD COLUMN meta_description TEXT NOT NULL DEFAULT ''")
        # Seed initial product if empty
        cur = conn.execute("SELECT COUNT(*) AS c FROM user_products")
        if cur.fetchone()["c"] == 0:
            now = utc_now()
            conn.execute("""INSERT INTO user_products (title, url, price, description, badge, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("Code to Career — The Python Fresher to Job-Ready Developer",
                 "https://codetocareer52.myinstamojo.com/product/code-to-career",
                 "₹499",
                 "Fast-track from beginner to an interview-ready, high-earning Python developer with 25+ real projects and mock guides.",
                 "★ Recommended Guide",
                 now, now))
        # Migrate existing databases created before PKCE support.
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(oauth_states)").fetchall()}
        if "code_verifier" not in columns:
            conn.execute("ALTER TABLE oauth_states ADD COLUMN code_verifier TEXT NOT NULL DEFAULT ''")

def save_article(*, topic: str, primary_keyword: str, title: str, markdown_body: str,
                 rendered_html: str = "", schema_json: dict[str, Any] | str | None = None,
                 status: str = "DRAFT", article_id: int | None = None,
                 blogger_post_id: str = "", blogger_blog_id: str = "",
                 meta_description: str | None = None) -> int:
    if status not in {"QUEUED","DRAFT","PAUSED","PUBLISHED"}: raise ValueError(f"Unsupported status: {status}")
    now = utc_now()
    schema_text = schema_json if isinstance(schema_json, str) else json.dumps(schema_json or {}, ensure_ascii=False)
    with connection() as conn:
        if article_id is not None:
            previous = conn.execute(
                "SELECT title,meta_description,markdown_body,rendered_html FROM articles WHERE id=?",
                (article_id,),
            ).fetchone()
            if previous is None:
                raise ValueError(f"Article {article_id} does not exist")
            cur = conn.execute("""UPDATE articles SET topic=?,primary_keyword=?,title=?,
              meta_description=COALESCE(?,meta_description),markdown_body=?,rendered_html=?,schema_json=?,status=?,
              blogger_post_id=CASE WHEN ?='' THEN blogger_post_id ELSE ? END,
              blogger_blog_id=CASE WHEN ?='' THEN blogger_blog_id ELSE ? END,updated_at=?,
              published_at=CASE WHEN ?='PUBLISHED' AND published_at='' THEN ? ELSE published_at END WHERE id=?""",
              (topic,primary_keyword,title,meta_description,markdown_body,rendered_html,schema_text,status,
               blogger_post_id,blogger_post_id,blogger_blog_id,blogger_blog_id,now,status,now,article_id))
            if cur.rowcount == 0: raise ValueError(f"Article {article_id} does not exist")
            if (
                previous["title"] != title
                or (meta_description is not None and previous["meta_description"] != meta_description)
                or previous["markdown_body"] != markdown_body
                or previous["rendered_html"] != rendered_html
            ):
                _save_article_revision(
                    conn, article_id, title,
                    meta_description if meta_description is not None else previous["meta_description"],
                    markdown_body, rendered_html, "saved", now
                )
            return article_id
        cur = conn.execute("""INSERT INTO articles(topic,primary_keyword,title,meta_description,markdown_body,rendered_html,
          schema_json,status,blogger_post_id,blogger_blog_id,created_at,updated_at,published_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (topic,primary_keyword,title,meta_description or "",markdown_body,rendered_html,schema_text,status,blogger_post_id,
           blogger_blog_id,now,now,now if status == "PUBLISHED" else ""))
        new_id = int(cur.lastrowid)
        _save_article_revision(
            conn, new_id, title, meta_description or "", markdown_body, rendered_html, "created", now
        )
        return new_id

def _save_article_revision(
    conn: sqlite3.Connection,
    article_id: int,
    title: str,
    meta_description: str,
    markdown_body: str,
    rendered_html: str,
    reason: str,
    created_at: str,
) -> None:
    revision_number = int(conn.execute(
        "SELECT COALESCE(MAX(revision_number),0)+1 FROM article_revisions WHERE article_id=?",
        (article_id,),
    ).fetchone()[0])
    conn.execute(
        """INSERT INTO article_revisions
        (article_id,revision_number,title,meta_description,markdown_body,rendered_html,reason,created_at)
        VALUES(?,?,?,?,?,?,?,?)""",
        (article_id,revision_number,title,meta_description,markdown_body,rendered_html,reason,created_at),
    )

def list_article_revisions(article_id: int, limit: int = 50) -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute(
            """SELECT id,article_id,revision_number,title,meta_description,markdown_body,rendered_html,reason,created_at
            FROM article_revisions WHERE article_id=?
            ORDER BY revision_number DESC LIMIT ?""",
            (article_id,max(1,min(limit,100))),
        ).fetchall()
    return [dict(row) for row in rows]

def save_quality_report(article_id: int, title: str, markdown_body: str,
                        report: dict[str, Any], meta_description: str = "") -> int:
    now = utc_now()
    digest = content_fingerprint(title, markdown_body, meta_description)
    with connection() as conn:
        current = conn.execute(
            "SELECT title,meta_description,markdown_body FROM articles WHERE id=?",(article_id,)
        ).fetchone()
        if not current:
            raise ValueError(f"Article {article_id} does not exist")
        current_digest = content_fingerprint(
            current["title"],current["markdown_body"],current["meta_description"]
        )
        if digest != current_digest:
            raise ValueError("Article changed while the quality review was running; run the review again.")
        cur = conn.execute(
            "INSERT INTO quality_reports(article_id,content_hash,report_json,created_at) VALUES(?,?,?,?)",
            (article_id,digest,json.dumps(report,ensure_ascii=False),now),
        )
        return int(cur.lastrowid)

def list_quality_reports(article_id: int, limit: int = 20) -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute(
            """SELECT id,article_id,content_hash,report_json,created_at
            FROM quality_reports WHERE article_id=? ORDER BY id DESC LIMIT ?""",
            (article_id,max(1,min(limit,100))),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["report"] = json.loads(item.pop("report_json"))
        result.append(item)
    return result

def save_review_decision(article_id: int, decision: str, notes: str = "") -> dict[str, Any]:
    if decision not in {"APPROVED","CHANGES_REQUESTED"}:
        raise ValueError(f"Unsupported review decision: {decision}")
    now = utc_now()
    with connection() as conn:
        article = conn.execute(
            "SELECT title,meta_description,markdown_body FROM articles WHERE id=?",(article_id,)
        ).fetchone()
        if not article:
            raise ValueError(f"Article {article_id} does not exist")
        digest = content_fingerprint(
            article["title"],article["markdown_body"],article["meta_description"]
        )
        latest_report = conn.execute(
            "SELECT content_hash FROM quality_reports WHERE article_id=? ORDER BY id DESC LIMIT 1",
            (article_id,),
        ).fetchone()
        if not latest_report or latest_report["content_hash"] != digest:
            raise ValueError("Run a fresh quality review of the current saved draft before recording a decision.")
        cur = conn.execute(
            """INSERT INTO review_decisions
            (article_id,content_hash,decision,notes,created_at) VALUES(?,?,?,?,?)""",
            (article_id,digest,decision,notes.strip(),now),
        )
        return {
            "id": int(cur.lastrowid),
            "article_id": article_id,
            "content_hash": digest,
            "decision": decision,
            "notes": notes.strip(),
            "created_at": now,
        }

def get_article_review_status(article_id: int) -> dict[str, Any]:
    with connection() as conn:
        article = conn.execute(
            "SELECT title,meta_description,markdown_body FROM articles WHERE id=?",(article_id,)
        ).fetchone()
        if not article:
            return {"status":"NOT_FOUND","decision":None}
        latest = conn.execute(
            """SELECT decision,notes,created_at,content_hash FROM review_decisions
            WHERE article_id=? ORDER BY id DESC LIMIT 1""",
            (article_id,),
        ).fetchone()
    if not latest:
        return {"status":"DRAFT","decision":None}
    current_hash = content_fingerprint(
        article["title"],article["markdown_body"],article["meta_description"]
    )
    if latest["content_hash"] != current_hash:
        return {"status":"NEEDS_REVIEW","decision":dict(latest)}
    return {"status":latest["decision"],"decision":dict(latest)}

def get_article(article_id: int) -> dict[str, Any] | None:
    with connection() as conn: row = conn.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()
    return dict(row) if row else None

def list_articles(limit: int = 500) -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM articles ORDER BY updated_at DESC LIMIT ?", (max(1,min(limit,2000)),)).fetchall()
    return [dict(r) for r in rows]

def delete_article(article_id: int, *, require_blogger_post: bool = False) -> bool:
    with connection() as conn:
        row = conn.execute(
            "SELECT blogger_post_id FROM articles WHERE id=?",
            (article_id,),
        ).fetchone()
        if row is None:
            return False
        if require_blogger_post and not row["blogger_post_id"]:
            raise ValueError("Only an article linked to a confirmed Blogger draft can be deleted this way.")
        conn.execute("DELETE FROM articles WHERE id=?", (article_id,))
        return True

def set_article_status(article_id: int, status: str) -> None:
    if status not in {"QUEUED","DRAFT","PAUSED","PUBLISHED"}: raise ValueError(f"Unsupported status: {status}")
    with connection() as conn:
        cur = conn.execute("UPDATE articles SET status=?,updated_at=? WHERE id=?", (status,utc_now(),article_id))
        if cur.rowcount == 0: raise ValueError(f"Article {article_id} does not exist")

def queue_article(article_id: int) -> int:
    now = utc_now()
    with connection() as conn:
        cur = conn.execute("INSERT INTO automation_queue(article_id,state,retry_count,max_retries,execution_log,updated_at) VALUES(?,?,?,?,?,?)",
          (article_id,"PAUSED",0,3,json.dumps([{"at":now,"event":"queued"}]),now))
        conn.execute("UPDATE articles SET status='QUEUED',updated_at=? WHERE id=?", (now,article_id))
        return int(cur.lastrowid)

def queue_state() -> str:
    with connection() as conn: rows = conn.execute("SELECT state FROM automation_queue ORDER BY id DESC LIMIT 100").fetchall()
    return "RUNNING" if any(r["state"] == "RUNNING" for r in rows) else "PAUSED"

def set_queue_state(state: str) -> None:
    if state not in {"RUNNING","PAUSED"}: raise ValueError("Queue state must be RUNNING or PAUSED")
    now = utc_now()
    with connection() as conn:
        rows = conn.execute("SELECT id,execution_log FROM automation_queue ORDER BY id DESC LIMIT 100").fetchall()
        for row in rows:
            log = _append_log(row["execution_log"], {"at":now,"event":state.lower()})
            conn.execute("UPDATE automation_queue SET state=?,execution_log=?,updated_at=? WHERE id=?",
                         (state,log,now,row["id"]))


def restart_queue() -> None:
    """Resume all queued work with fresh retry counters and an audit event."""
    now = utc_now()
    with connection() as conn:
        rows = conn.execute("SELECT id,execution_log FROM automation_queue").fetchall()
        for row in rows:
            conn.execute("UPDATE automation_queue SET state='RUNNING',retry_count=0,updated_at=?,execution_log=? WHERE id=?",
                         (now,_append_log(row["execution_log"],{"at":now,"event":"restarted"}),row["id"]))

def _append_log(existing: str, entry: dict[str, Any]) -> str:
    try: events = json.loads(existing or "[]")
    except (TypeError,json.JSONDecodeError): events = []
    if not isinstance(events,list): events = []
    events.append(entry)
    return json.dumps(events[-200:],ensure_ascii=False)

def queue_rows() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("""SELECT q.*,a.title,a.topic,a.primary_keyword,a.status AS article_status
          FROM automation_queue q LEFT JOIN articles a ON a.id=q.article_id ORDER BY q.updated_at DESC LIMIT 200""").fetchall()
    return [dict(r) for r in rows]

def log_queue_event(queue_id: int, event: str, *, retry: bool = False, state: str | None = None) -> None:
    now = utc_now()
    if state is not None and state not in {"RUNNING", "PAUSED"}:
        raise ValueError("Queue item state must be RUNNING or PAUSED")
    with connection() as conn:
        row = conn.execute("SELECT execution_log,retry_count FROM automation_queue WHERE id=?", (queue_id,)).fetchone()
        if not row: return
        count = int(row["retry_count"]) + (1 if retry else 0)
        log = _append_log(row["execution_log"], {"at": now, "event": event})
        if state is None:
            conn.execute("UPDATE automation_queue SET execution_log=?,retry_count=?,updated_at=? WHERE id=?",
                         (log,count,now,queue_id))
        else:
            conn.execute("UPDATE automation_queue SET state=?,execution_log=?,retry_count=?,updated_at=? WHERE id=?",
                         (state,log,count,now,queue_id))

def save_affiliate(product_name: str, keywords: list[str], tracking_url: str, disclosure: str,
                   affiliate_id: int | None = None) -> int:
    now = utc_now()
    with connection() as conn:
        if affiliate_id:
            cur = conn.execute("UPDATE affiliate_vault SET product_name=?,trigger_keywords=?,tracking_url=?,disclosure_snippet=?,updated_at=? WHERE id=?",
              (product_name.strip(),json.dumps(keywords),tracking_url.strip(),disclosure.strip(),now,affiliate_id))
            if cur.rowcount == 0: raise ValueError("Affiliate entry not found")
            return affiliate_id
        cur = conn.execute("INSERT INTO affiliate_vault(product_name,trigger_keywords,tracking_url,disclosure_snippet,created_at,updated_at) VALUES(?,?,?,?,?,?)",
          (product_name.strip(),json.dumps(keywords),tracking_url.strip(),disclosure.strip(),now,now))
        return int(cur.lastrowid)

def list_affiliates() -> list[dict[str, Any]]:
    with connection() as conn: rows = conn.execute("SELECT * FROM affiliate_vault ORDER BY updated_at DESC").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        try: item["trigger_keywords_list"] = json.loads(item["trigger_keywords"])
        except (TypeError,json.JSONDecodeError): item["trigger_keywords_list"] = []
        result.append(item)
    return result

def delete_affiliate(affiliate_id: int) -> bool:
    with connection() as conn:
        cur = conn.execute("DELETE FROM affiliate_vault WHERE id=?", (affiliate_id,))
        return cur.rowcount > 0

def list_products() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM user_products ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]

def get_product(product_id: int) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM user_products WHERE id=?", (product_id,)).fetchone()
        return dict(row) if row else None

def save_product(*, title: str, url: str, price: str = "", description: str = "",
                 badge: str = "Recommended Guide", product_id: int | None = None) -> int:
    now = utc_now()
    with connection() as conn:
        if product_id:
            cur = conn.execute("""UPDATE user_products SET title=?, url=?, price=?, description=?, badge=?, updated_at=?
                WHERE id=?""", (title.strip(), url.strip(), price.strip(), description.strip(), badge.strip(), now, product_id))
            if cur.rowcount == 0:
                raise ValueError("Product not found")
            return product_id
        cur = conn.execute("""INSERT INTO user_products (title, url, price, description, badge, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title.strip(), url.strip(), price.strip(), description.strip(), badge.strip(), now, now))
        return int(cur.lastrowid)

def delete_product(product_id: int) -> bool:
    with connection() as conn:
        cur = conn.execute("DELETE FROM user_products WHERE id=?", (product_id,))
        return cur.rowcount > 0

def store_oauth_state(state: str, code_verifier: str = "") -> None:
    """Persist short-lived OAuth state and its PKCE verifier across the Google redirect."""
    now = utc_now()
    with connection() as conn:
        conn.execute("DELETE FROM oauth_states WHERE created_at < datetime('now', '-15 minutes')")
        conn.execute("INSERT OR REPLACE INTO oauth_states(state,created_at,code_verifier) VALUES(?,?,?)",
                     (state, now, code_verifier))

def consume_oauth_state(state: str) -> str | None:
    """Validate and consume OAuth state once; return its PKCE verifier."""
    if not state:
        return None
    with connection() as conn:
        row = conn.execute("SELECT created_at,code_verifier FROM oauth_states WHERE state=?", (state,)).fetchone()
        if not row:
            return None
        conn.execute("DELETE FROM oauth_states WHERE state=?", (state,))
        try:
            created = datetime.fromisoformat(row["created_at"])
            if (datetime.now(timezone.utc) - created).total_seconds() > 900:
                return None
        except (ValueError, TypeError):
            return None
        verifier = row["code_verifier"]
        return verifier or None

def save_system_credential(key: str, value: str) -> None:
    now = utc_now()
    with connection() as conn:
        conn.execute("INSERT OR REPLACE INTO system_credentials(key, value, updated_at) VALUES(?,?,?)",
                     (key, value, now))

def get_system_credential(key: str) -> str | None:
    with connection() as conn:
        row = conn.execute("SELECT value FROM system_credentials WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None
