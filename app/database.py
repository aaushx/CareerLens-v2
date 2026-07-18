import json
import os
import sqlite3

# Support environment variable for database path, default to careerlens.db
DB_PATH = os.getenv("DATABASE_PATH", "careerlens.db")


def get_db_connection(db_path: str | None = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | None = None) -> None:
    """Initializes the database and creates the scans table if it doesn't exist."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    filename TEXT,
                    extraction_method TEXT,
                    job_description TEXT,
                    final_score REAL,
                    skill_match REAL,
                    semantic_match REAL,
                    resume_strength REAL,
                    badge TEXT,
                    results_json TEXT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_scans_session_timestamp ON scans(session_id, timestamp DESC)
            """)
    finally:
        conn.close()


def save_scan(
    session_id: str,
    filename: str,
    extraction_method: str,
    job_description: str,
    results: dict,
    db_path: str | None = None,
) -> int:
    """Saves a new scan to the database and returns the generated scan ID."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()

            # Extract metrics for top-level columns
            metrics = results.get("metrics", {})
            final_score = metrics.get("final_score", 0.0)
            skill_match = metrics.get("skill_match", 0.0)
            semantic_match = metrics.get("semantic_match", 0.0)
            resume_strength = metrics.get("resume_strength", 0.0)
            badge = metrics.get("badge", "Beginner")

            cursor.execute(
                """
                INSERT INTO scans (session_id, filename, extraction_method, job_description, final_score, skill_match, semantic_match, resume_strength, badge, results_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    filename,
                    extraction_method,
                    job_description,
                    final_score,
                    skill_match,
                    semantic_match,
                    resume_strength,
                    badge,
                    json.dumps(results),
                ),
            )

            last_id = cursor.lastrowid
            return last_id if last_id is not None else 0
    finally:
        conn.close()


def get_scans(session_id: str, db_path: str | None = None) -> list[dict]:
    """Retrieves all scan summaries for a specific session."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, timestamp, filename, extraction_method, final_score, skill_match, semantic_match, resume_strength, badge
            FROM scans
            WHERE session_id = ?
            ORDER BY timestamp DESC
        """,
            (session_id,),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    scans_list = []
    for row in rows:
        scans_list.append(
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "filename": row["filename"],
                "extraction_method": row["extraction_method"],
                "final_score": row["final_score"],
                "skill_match": row["skill_match"],
                "semantic_match": row["semantic_match"],
                "resume_strength": row["resume_strength"],
                "badge": row["badge"],
            }
        )
    return scans_list


def get_scan(scan_id: int, session_id: str, db_path: str | None = None) -> dict | None:
    """Retrieves the full JSON payload for a single scan, verifying session ownership."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT results_json
            FROM scans
            WHERE id = ? AND session_id = ?
        """,
            (scan_id, session_id),
        )
        row = cursor.fetchone()
    finally:
        conn.close()

    if row:
        res = json.loads(row["results_json"])
        if isinstance(res, dict):
            return res
    return None


def clear_scans(session_id: str, db_path: str | None = None) -> None:
    """Deletes all scans associated with a session."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM scans
                WHERE session_id = ?
            """,
                (session_id,),
            )
    finally:
        conn.close()
