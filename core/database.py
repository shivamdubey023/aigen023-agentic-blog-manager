"""Core persistence and application services."""
from __future__ import annotations
import json, os, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

APP_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get("CONTENT_OPS_DB", APP_ROOT / "content_ops.db"))

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=15, isolation_level="DEFERRED")
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
          markdown_body TEXT NOT NULL DEFAULT '', rendered_html TEXT NOT NULL DEFAULT '',
          schema_json TEXT NOT NULL DEFAULT '{}',
          status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(status IN ('QUEUED','DRAFT','PAUSED','PUBLISHED')),
          blogger_post_id TEXT NOT NULL DEFAULT '', blogger_blog_id TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL, published_at TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
        CREATE INDEX IF NOT EXISTS idx_articles_updated ON articles(updated_at DESC);
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
        """)

def save_article(*, topic: str, primary_keyword: str, title: str, markdown_body: str,
                 rendered_html: str = "", schema_json: dict[str, Any] | str | None = None,
                 status: str = "DRAFT", article_id: int | None = None,
                 blogger_post_id: str = "", blogger_blog_id: str = "") -> int:
    if status not in {"QUEUED","DRAFT","PAUSED","PUBLISHED"}: raise ValueError(f"Unsupported status: {status}")
    now = utc_now()
    schema_text = schema_json if isinstance(schema_json, str) else json.dumps(schema_json or {}, ensure_ascii=False)
    with connection() as conn:
        if article_id is not None:
            cur = conn.execute("""UPDATE articles SET topic=?,primary_keyword=?,title=?,markdown_body=?,
              rendered_html=?,schema_json=?,status=?,blogger_post_id=?,blogger_blog_id=?,updated_at=?,
              published_at=CASE WHEN ?='PUBLISHED' AND published_at='' THEN ? ELSE published_at END WHERE id=?""",
              (topic,primary_keyword,title,markdown_body,rendered_html,schema_text,status,blogger_post_id,
               blogger_blog_id,now,status,now,article_id))
            if cur.rowcount == 0: raise ValueError(f"Article {article_id} does not exist")
            return article_id
        cur = conn.execute("""INSERT INTO articles(topic,primary_keyword,title,markdown_body,rendered_html,
          schema_json,status,blogger_post_id,blogger_blog_id,created_at,updated_at,published_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
          (topic,primary_keyword,title,markdown_body,rendered_html,schema_text,status,blogger_post_id,
           blogger_blog_id,now,now,now if status == "PUBLISHED" else ""))
        return int(cur.lastrowid)

def get_article(article_id: int) -> dict[str, Any] | None:
    with connection() as conn: row = conn.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()
    return dict(row) if row else None

def list_articles(limit: int = 500) -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM articles ORDER BY updated_at DESC LIMIT ?", (max(1,min(limit,2000)),)).fetchall()
    return [dict(r) for r in rows]

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
