import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/logistics.db")


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id            INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp         TEXT    NOT NULL,
                status            TEXT    NOT NULL DEFAULT 'running',
                step              TEXT    DEFAULT '',
                error             TEXT,
                agents_completed  TEXT    DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS shipments (
                id                              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id                          INTEGER NOT NULL REFERENCES pipeline_runs(run_id),
                shipment_id                     TEXT    NOT NULL,
                run_date                        TEXT,
                country                         TEXT,
                postcode                        TEXT,
                sla_tier                        TEXT,
                address_complete                INTEGER DEFAULT 1,
                is_vip                          INTEGER DEFAULT 0,
                order_value_eur                 REAL    DEFAULT 0,
                regional_delay                  INTEGER DEFAULT 0,
                courier                         TEXT,
                courier_otd_rate                REAL    DEFAULT 0,
                status                          TEXT,
                attempt_count                   INTEGER DEFAULT 0,
                sla_deadline                    TEXT,
                exceptions_list                 TEXT    DEFAULT '[]',
                exception_type                  TEXT,
                severity                        TEXT,
                recommended_action              TEXT,
                disposition                     TEXT,
                escalation_reason               TEXT,
                exception_timestamp             TEXT,
                ui_status                       TEXT,
                regen_count                     INTEGER DEFAULT 0,
                regen_history                   TEXT    DEFAULT '[]',
                a3_data                         TEXT,
                a4_data                         TEXT
            );

            CREATE TABLE IF NOT EXISTS decisions (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id              INTEGER REFERENCES pipeline_runs(run_id),
                timestamp           TEXT    NOT NULL,
                shipment_id         TEXT    NOT NULL,
                courier             TEXT    DEFAULT '',
                country             TEXT    DEFAULT '',
                issue_type          TEXT    DEFAULT '',
                urgency             TEXT    DEFAULT '',
                resolution          TEXT    DEFAULT '',
                decision            TEXT    DEFAULT '',
                message_sent        TEXT    DEFAULT '',
                channel             TEXT    DEFAULT '',
                production_note     TEXT    DEFAULT '',
                reject_reason       TEXT    DEFAULT '',
                modify_instruction  TEXT    DEFAULT '',
                tokens_used         INTEGER DEFAULT 0,
                composite_score     REAL    DEFAULT 0,
                order_value_eur     REAL    DEFAULT 0,
                is_vip              INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS scorecard (
                id                              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id                          INTEGER NOT NULL REFERENCES pipeline_runs(run_id),
                last_run                        TEXT,
                courier                         TEXT    NOT NULL,
                total_shipments                 INTEGER DEFAULT 0,
                otd_rate                        REAL    DEFAULT 0,
                courier_attributable_miss       INTEGER DEFAULT 0,
                non_courier_attributable_miss   INTEGER DEFAULT 0,
                attrib_exc_rate                 REAL    DEFAULT 0,
                total_exceptions                INTEGER DEFAULT 0,
                composite_flag                  INTEGER DEFAULT 0,
                rating                          TEXT    DEFAULT '',
                recommendation                  TEXT    DEFAULT ''
            );
        """)


# ── Write helpers ──────────────────────────────────────────────────────────────

def start_pipeline_run(conn: sqlite3.Connection) -> int:
    cur = conn.execute(
        "INSERT INTO pipeline_runs (timestamp, status, step) VALUES (?, 'running', 'Starting...')",
        (datetime.now().isoformat(),),
    )
    conn.commit()
    return cur.lastrowid


def update_pipeline_status(
    conn: sqlite3.Connection,
    run_id: int,
    step: str,
    error: str = None,
    status: str = "running",
    agents_completed: list = None,
) -> None:
    agents_json = json.dumps(agents_completed) if agents_completed is not None else None
    if agents_json is not None:
        conn.execute(
            "UPDATE pipeline_runs SET step=?, error=?, status=?, agents_completed=? WHERE run_id=?",
            (step, error, status, agents_json, run_id),
        )
    else:
        conn.execute(
            "UPDATE pipeline_runs SET step=?, error=?, status=? WHERE run_id=?",
            (step, error, status, run_id),
        )
    conn.commit()


def insert_shipment_log(
    conn: sqlite3.Connection,
    run_id: int,
    shipments: list,
    exc_map: dict,
) -> None:
    rows = []
    for s in shipments:
        sla = s.get("sla_deadline", "")
        if hasattr(sla, "isoformat"):
            sla = sla.isoformat()
        rows.append((
            run_id,
            s["shipment_id"],
            s.get("run_date", datetime.now().strftime("%Y-%m-%d")),
            s.get("country"), s.get("postcode"), s.get("sla_tier"),
            int(bool(s.get("address_complete", True))),
            int(bool(s.get("is_vip", False))),
            float(s.get("order_value_eur", 0)),
            int(bool(s.get("regional_delay", False))),
            s.get("courier"), float(s.get("courier_otd_rate", 0)),
            s.get("status"), int(s.get("attempt_count", 0)), sla,
            json.dumps(exc_map.get(s["shipment_id"], [])),
        ))
    conn.executemany(
        """INSERT INTO shipments
           (run_id, shipment_id, run_date, country, postcode, sla_tier,
            address_complete, is_vip, order_value_eur, regional_delay,
            courier, courier_otd_rate, status, attempt_count, sla_deadline,
            exceptions_list)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()


def update_exception_data(
    conn: sqlite3.Connection,
    run_id: int,
    shipment_id: str,
    exception_type: str,
    severity: str,
    recommended_action: str,
    disposition: str,
    escalation_reason: str,
    exception_timestamp: str,
    ui_status: str,
    a3_data: dict,
    a4_data: dict,
) -> None:
    conn.execute(
        """UPDATE shipments SET
               exception_type=?, severity=?, recommended_action=?,
               disposition=?, escalation_reason=?, exception_timestamp=?,
               ui_status=?, a3_data=?, a4_data=?, regen_count=0, regen_history='[]'
           WHERE run_id=? AND shipment_id=?""",
        (
            exception_type, severity, recommended_action,
            disposition, escalation_reason, exception_timestamp,
            ui_status,
            json.dumps(a3_data), json.dumps(a4_data),
            run_id, shipment_id,
        ),
    )
    conn.commit()


def insert_decisions_bulk(
    conn: sqlite3.Connection,
    run_id: int,
    decisions: list,
) -> None:
    rows = [_decision_to_row(d, run_id) for d in decisions]
    conn.executemany(_DECISION_INSERT_SQL, rows)
    conn.commit()


def insert_scorecard(
    conn: sqlite3.Connection,
    run_id: int,
    last_run: str,
    scorecard_list: list,
) -> None:
    rows = [(
        run_id, last_run,
        c["courier"],
        c.get("total_shipments", 0),
        c.get("otd_rate", 0),
        c.get("courier_attributable_miss", 0),
        c.get("non_courier_attributable_miss", 0),
        c.get("attrib_exc_rate", 0),
        c.get("total_exceptions", 0),
        int(bool(c.get("composite_flag", False))),
        c.get("rating", ""),
        c.get("recommendation", ""),
    ) for c in scorecard_list]
    conn.executemany(
        """INSERT INTO scorecard
           (run_id, last_run, courier, total_shipments, otd_rate,
            courier_attributable_miss, non_courier_attributable_miss,
            attrib_exc_rate, total_exceptions, composite_flag, rating, recommendation)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()


def update_exception_ui_status(
    conn: sqlite3.Connection,
    shipment_id: str,
    new_status: str,
) -> None:
    # Updates the most recent run's record for this shipment
    conn.execute(
        """UPDATE shipments SET ui_status=?
           WHERE shipment_id=? AND run_id=(
               SELECT MAX(run_id) FROM shipments WHERE shipment_id=?
           )""",
        (new_status, shipment_id, shipment_id),
    )
    conn.commit()


_DECISION_INSERT_SQL = """INSERT INTO decisions
    (run_id, timestamp, shipment_id, courier, country, issue_type, urgency,
     resolution, decision, message_sent, channel, production_note,
     reject_reason, modify_instruction, tokens_used, composite_score,
     order_value_eur, is_vip)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""


def _decision_to_row(d: dict, run_id: int = None) -> tuple:
    return (
        run_id,
        d.get("timestamp", ""),
        d.get("shipment_id", ""),
        d.get("courier", ""),
        d.get("country", ""),
        d.get("issue_type", ""),
        d.get("urgency", ""),
        d.get("resolution", ""),
        d.get("decision", ""),
        d.get("message_sent", ""),
        d.get("channel", ""),
        d.get("production_note", ""),
        d.get("reject_reason", ""),
        d.get("modify_instruction", ""),
        int(d.get("tokens_used", 0)),
        float(d.get("composite_score", 0)),
        float(d.get("order_value_eur", 0)),
        int(bool(d.get("is_vip", False))),
    )


def insert_decision(conn: sqlite3.Connection, d: dict, run_id: int = None) -> None:
    conn.execute(_DECISION_INSERT_SQL, _decision_to_row(d, run_id))
    conn.commit()


def update_empathy(
    conn: sqlite3.Connection,
    shipment_id: str,
    empathy_text: str,
    regen_count: int,
    regen_history: list,
) -> None:
    # Fetch current a4_data, update empathy_text inside it, then write back
    row = conn.execute(
        """SELECT a4_data FROM shipments WHERE shipment_id=? AND run_id=(
               SELECT MAX(run_id) FROM shipments WHERE shipment_id=?
           )""",
        (shipment_id, shipment_id),
    ).fetchone()
    if row is None:
        return
    a4 = json.loads(row["a4_data"]) if row["a4_data"] else {}
    a4["empathy_text"] = empathy_text
    conn.execute(
        """UPDATE shipments SET a4_data=?, regen_count=?, regen_history=?
           WHERE shipment_id=? AND run_id=(
               SELECT MAX(run_id) FROM shipments WHERE shipment_id=?
           )""",
        (json.dumps(a4), regen_count, json.dumps(regen_history), shipment_id, shipment_id),
    )
    conn.commit()


# ── Read helpers ───────────────────────────────────────────────────────────────

def _get_latest_run(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM pipeline_runs ORDER BY run_id DESC LIMIT 1"
    ).fetchone()


def get_results(conn: sqlite3.Connection) -> dict:
    run = _get_latest_run(conn)
    if run is None:
        return {}

    rows = conn.execute(
        "SELECT * FROM shipments WHERE run_id=? AND exception_type IS NOT NULL",
        (run["run_id"],),
    ).fetchall()

    exceptions = []
    escalated = []
    auto_handled = []

    for r in rows:
        a3 = json.loads(r["a3_data"]) if r["a3_data"] else {}
        a4 = json.loads(r["a4_data"]) if r["a4_data"] else {}
        regen_history = json.loads(r["regen_history"]) if r["regen_history"] else []

        shipment_dict = {
            "shipment_id": r["shipment_id"],
            "country": r["country"],
            "postcode": r["postcode"],
            "sla_tier": r["sla_tier"],
            "address_complete": bool(r["address_complete"]),
            "is_vip": bool(r["is_vip"]),
            "order_value_eur": r["order_value_eur"],
            "regional_delay": bool(r["regional_delay"]),
            "courier": r["courier"],
            "courier_otd_rate": r["courier_otd_rate"],
            "status": r["status"],
            "attempt_count": r["attempt_count"],
            "sla_deadline": r["sla_deadline"],
        }

        exc = {
            "exception_type": r["exception_type"],
            "severity": r["severity"],
            "shipment_id": r["shipment_id"],
            "shipment": shipment_dict,
            "recommended_action": r["recommended_action"],
            "disposition": r["disposition"],
            "escalation_reason": r["escalation_reason"],
            "timestamp": r["exception_timestamp"],
            "a3": a3,
            "a4": a4,
            "ui_status": r["ui_status"],
            "regen_count": r["regen_count"] or 0,
            "regen_history": regen_history,
        }
        exceptions.append(exc)

        ui = r["ui_status"]
        if ui == "needs_decision":
            escalated.append(r["shipment_id"])
        elif ui == "auto_handled":
            auto_handled.append(r["shipment_id"])

    decisions_made = sum(
        1 for e in exceptions if e["ui_status"] == "decided"
    )
    stats = {
        "total_issues": len(exceptions),
        "auto_handled": len(auto_handled),
        "needs_decision": len(escalated),
        "decisions_made": decisions_made,
        "sent_to_supervisor": 0,
    }

    ps = run["status"]
    pipeline_status = {
        "step": run["step"] or "",
        "running": ps == "running",
        "error": run["error"],
    }

    return {
        "last_run": run["timestamp"],
        "pipeline_status": pipeline_status,
        "exceptions": exceptions,
        "escalated": escalated,
        "auto_handled": auto_handled,
        "stats": stats,
    }


def get_scorecard_data(conn: sqlite3.Connection) -> dict:
    run = _get_latest_run(conn)
    if run is None:
        return {}

    rows = conn.execute(
        "SELECT * FROM scorecard WHERE run_id=?", (run["run_id"],)
    ).fetchall()

    last_run = rows[0]["last_run"] if rows else run["timestamp"]
    scorecard_list = [
        {
            "courier": r["courier"],
            "total_shipments": r["total_shipments"],
            "otd_rate": r["otd_rate"],
            "courier_attributable_miss": r["courier_attributable_miss"],
            "non_courier_attributable_miss": r["non_courier_attributable_miss"],
            "attrib_exc_rate": r["attrib_exc_rate"],
            "total_exceptions": r["total_exceptions"],
            "composite_flag": bool(r["composite_flag"]),
            "rating": r["rating"],
            "recommendation": r["recommendation"],
        }
        for r in rows
    ]
    return {"last_run": last_run, "scorecard": scorecard_list}


def get_all_decisions(conn: sqlite3.Connection) -> list:
    rows = conn.execute(
        "SELECT * FROM decisions ORDER BY timestamp DESC"
    ).fetchall()
    return [
        {
            "timestamp": r["timestamp"],
            "shipment_id": r["shipment_id"],
            "courier": r["courier"],
            "country": r["country"],
            "issue_type": r["issue_type"],
            "urgency": r["urgency"],
            "resolution": r["resolution"],
            "decision": r["decision"],
            "message_sent": r["message_sent"],
            "channel": r["channel"],
            "production_note": r["production_note"],
            "reject_reason": r["reject_reason"],
            "modify_instruction": r["modify_instruction"],
            "tokens_used": r["tokens_used"],
            "composite_score": r["composite_score"],
            "order_value_eur": r["order_value_eur"],
            "is_vip": bool(r["is_vip"]),
        }
        for r in rows
    ]


def get_shipment_log(conn: sqlite3.Connection) -> list:
    """Returns log-style rows for all shipments (used by courier_performance_agent)."""
    rows = conn.execute(
        "SELECT * FROM shipments WHERE exceptions_list IS NOT NULL"
    ).fetchall()
    result = []
    for r in rows:
        entry = {
            "shipment_id": r["shipment_id"],
            "country": r["country"],
            "postcode": r["postcode"],
            "sla_tier": r["sla_tier"],
            "address_complete": bool(r["address_complete"]),
            "is_vip": bool(r["is_vip"]),
            "order_value_eur": r["order_value_eur"],
            "regional_delay": bool(r["regional_delay"]),
            "courier": r["courier"],
            "courier_otd_rate": r["courier_otd_rate"],
            "status": r["status"],
            "attempt_count": r["attempt_count"],
            "sla_deadline": r["sla_deadline"],
            "run_date": r["run_date"],
            "exceptions": json.loads(r["exceptions_list"]) if r["exceptions_list"] else [],
        }
        result.append(entry)
    return result


def count_distinct_run_dates(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COUNT(DISTINCT run_date) AS n FROM shipments WHERE run_date IS NOT NULL"
    ).fetchone()
    return row["n"] if row else 0
