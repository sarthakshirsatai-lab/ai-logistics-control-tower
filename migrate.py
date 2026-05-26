"""
One-time migration: JSON files → SQLite.
Safe to re-run — checks existing data before inserting.
"""

import json
from pathlib import Path

import database as db

DATA = Path("data")
RESULTS_F   = DATA / "results.json"
DECISIONS_F = DATA / "decisions.json"
SCORECARD_F = DATA / "scorecard.json"
LOG_F       = DATA / "shipment_log.json"


def _read(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _already_migrated(conn) -> bool:
    row = conn.execute("SELECT COUNT(*) AS n FROM pipeline_runs").fetchone()
    return row["n"] > 0


def migrate():
    db.init_db()
    conn = db.get_conn()

    if _already_migrated(conn):
        print("Database already contains data. Skipping migration to avoid duplicates.")
        print("Delete data/logistics.db and re-run to force a fresh migration.")
        return

    # ── 1. Migrate shipment_log.json ──────────────────────────────────────────
    log = _read(LOG_F, [])
    if log:
        # Group entries by run_date so each date gets its own pipeline_run row
        runs_by_date: dict[str, list] = {}
        for entry in log:
            date = entry.get("run_date", "unknown")
            runs_by_date.setdefault(date, []).append(entry)

        for run_date in sorted(runs_by_date):
            entries = runs_by_date[run_date]
            cur = conn.execute(
                "INSERT INTO pipeline_runs (timestamp, status, step, agents_completed) "
                "VALUES (?, 'complete', 'Migrated from shipment_log.json', '[]')",
                (run_date + "T00:00:00",),
            )
            conn.commit()
            run_id = cur.lastrowid

            rows = []
            for e in entries:
                sla = e.get("sla_deadline", "")
                rows.append((
                    run_id,
                    e["shipment_id"],
                    e.get("run_date"),
                    e.get("country"), e.get("postcode"), e.get("sla_tier"),
                    int(bool(e.get("address_complete", True))),
                    int(bool(e.get("is_vip", False))),
                    float(e.get("order_value_eur", 0)),
                    int(bool(e.get("regional_delay", False))),
                    e.get("courier"), float(e.get("courier_otd_rate", 0)),
                    e.get("status"), int(e.get("attempt_count", 0)), sla,
                    json.dumps(e.get("exceptions", [])),
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

        print(f"  shipment_log.json : {len(log)} shipment rows across "
              f"{len(runs_by_date)} run dates")
    else:
        print("  shipment_log.json : not found or empty — skipped")

    # ── 2. Migrate results.json exceptions ────────────────────────────────────
    results = _read(RESULTS_F, {})
    if results and isinstance(results, dict):
        last_run_ts = results.get("last_run", "")
        cur = conn.execute(
            "INSERT INTO pipeline_runs (timestamp, status, step, agents_completed) "
            "VALUES (?, 'complete', 'Migrated from results.json', "
            "'[\"Agent1\",\"Agent2\",\"Agent3\",\"Agent4\"]')",
            (last_run_ts,),
        )
        conn.commit()
        results_run_id = cur.lastrowid

        exceptions = results.get("exceptions", [])
        exc_inserted = 0
        for exc in exceptions:
            s = exc.get("shipment", {})
            sla = s.get("sla_deadline", "")
            a3 = exc.get("a3", {})
            a4 = exc.get("a4", {})

            # Determine exceptions_list from exception_type
            exc_type = exc.get("exception_type")
            exc_list = [exc_type] if exc_type else []

            conn.execute(
                """INSERT INTO shipments
                   (run_id, shipment_id, run_date, country, postcode, sla_tier,
                    address_complete, is_vip, order_value_eur, regional_delay,
                    courier, courier_otd_rate, status, attempt_count, sla_deadline,
                    exceptions_list,
                    exception_type, severity, recommended_action,
                    disposition, escalation_reason, exception_timestamp,
                    ui_status, regen_count, regen_history, a3_data, a4_data)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    results_run_id,
                    exc.get("shipment_id"),
                    last_run_ts[:10],            # run_date from timestamp
                    s.get("country"), s.get("postcode"), s.get("sla_tier"),
                    int(bool(s.get("address_complete", True))),
                    int(bool(s.get("is_vip", False))),
                    float(s.get("order_value_eur", 0)),
                    int(bool(s.get("regional_delay", False))),
                    s.get("courier"), float(s.get("courier_otd_rate", 0)),
                    s.get("status"), int(s.get("attempt_count", 0)), sla,
                    json.dumps(exc_list),
                    exc_type,
                    exc.get("severity"),
                    exc.get("recommended_action"),
                    exc.get("disposition"),
                    exc.get("escalation_reason"),
                    exc.get("timestamp"),
                    exc.get("ui_status"),
                    int(exc.get("regen_count", 0)),
                    json.dumps(exc.get("regen_history", [])),
                    json.dumps(a3) if a3 else None,
                    json.dumps(a4) if a4 else None,
                ),
            )
            exc_inserted += 1
        conn.commit()
        print(f"  results.json      : {exc_inserted} exception rows (run_id={results_run_id})")
    else:
        results_run_id = None
        print("  results.json      : not found or empty — skipped")

    # ── 3. Migrate decisions.json ─────────────────────────────────────────────
    decisions = _read(DECISIONS_F, [])
    if decisions and isinstance(decisions, list):
        rows = [db._decision_to_row(d, results_run_id) for d in decisions]
        conn.executemany(db._DECISION_INSERT_SQL, rows)
        conn.commit()
        print(f"  decisions.json    : {len(rows)} decision rows")
    else:
        print("  decisions.json    : not found or empty — skipped")

    # ── 4. Migrate scorecard.json ─────────────────────────────────────────────
    sc_data = _read(SCORECARD_F, {})
    if sc_data and isinstance(sc_data, dict) and results_run_id:
        sc_list = sc_data.get("scorecard", [])
        last_run = sc_data.get("last_run", "")
        db.insert_scorecard(conn, results_run_id, last_run, sc_list)
        print(f"  scorecard.json    : {len(sc_list)} courier rows")
    else:
        print("  scorecard.json    : not found or empty — skipped")

    # ── Summary ───────────────────────────────────────────────────────────────
    totals = {
        tbl: conn.execute(f"SELECT COUNT(*) AS n FROM {tbl}").fetchone()["n"]
        for tbl in ("pipeline_runs", "shipments", "decisions", "scorecard")
    }
    print("\nMigration complete:")
    for tbl, n in totals.items():
        print(f"  {tbl:<20} {n} rows")
    conn.close()


if __name__ == "__main__":
    migrate()
