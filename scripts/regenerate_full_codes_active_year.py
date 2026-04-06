#!/usr/bin/env python3
"""Regenerate FULL access codes for eligible students in active academic year.

Rules:
- student active
- finance_profile.is_eligible = 1
- student.academic_year_id == active academic year id (latest active)
- last code is full and expired, OR no code

Usage:
    python scripts/regenerate_full_codes_active_year.py
"""
import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import DatabaseConnection
from app.services.finance.finance_service import FinanceService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _d(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return datetime.fromisoformat(str(v)).date()
    except Exception:
        return None


def _get_active_year(db: DatabaseConnection):
    rows = db.execute_query(
        """
        SELECT academic_year_id, year_name, created_at
        FROM academic_year
        WHERE is_active = 1
        ORDER BY created_at DESC
        LIMIT 1
        """
    )
    return rows[0] if rows else None


def _get_targets(db: DatabaseConnection, active_year_id: int):
    query = """
        SELECT
            s.id,
            s.student_number,
            s.firstname,
            s.lastname,
            s.academic_year_id,
            COALESCE(fp.is_eligible, 0) AS is_eligible,
            ach.access_code AS last_access_code,
            ach.access_type AS last_access_type,
            ach.expires_at AS last_expires_at
        FROM student s
        JOIN finance_profile fp ON fp.student_id = s.id
        LEFT JOIN (
            SELECT x.student_id, x.access_code, x.access_type, x.expires_at, x.issued_at
            FROM access_code_history x
            INNER JOIN (
                SELECT student_id, MAX(issued_at) AS max_issued
                FROM access_code_history
                GROUP BY student_id
            ) m ON m.student_id = x.student_id AND m.max_issued = x.issued_at
        ) ach ON ach.student_id = s.id
        WHERE COALESCE(s.is_active, 1) = 1
          AND COALESCE(fp.is_eligible, 0) = 1
          AND s.academic_year_id = %s
        ORDER BY s.id
    """
    rows = db.execute_query(query, (active_year_id,)) or []

    today = date.today()
    targets = []
    for r in rows:
        last_type = (r.get("last_access_type") or "").lower()
        exp = _d(r.get("last_expires_at"))

        needs_regen = False
        if not r.get("last_access_code"):
            needs_regen = True
        elif last_type != "full":
            needs_regen = True
        elif exp is not None and exp < today:
            needs_regen = True

        if needs_regen:
            targets.append(r)

    return targets


def main() -> int:
    db = DatabaseConnection()
    finance = FinanceService()

    active = _get_active_year(db)
    if not active:
        print("Aucune année académique active trouvée. Abandon.")
        return 1

    active_year_id = active["academic_year_id"]
    active_year_name = active.get("year_name") or str(active_year_id)

    targets = _get_targets(db, active_year_id)
    print(f"Année active: {active_year_name} (ID={active_year_id})")
    print(f"Étudiants à régénérer: {len(targets)}")

    if not targets:
        print("Rien à régénérer.")
        return 0

    print("\n--- Régénération ---")
    generated = []

    for t in targets:
        sid = t["id"]
        name = f"{t.get('firstname','')} {t.get('lastname','')}".strip()
        try:
            finance._issue_access_code_if_needed(sid, True)
            row = db.execute_query(
                """
                SELECT access_code, access_type, expires_at, issued_at
                FROM access_code_history
                WHERE student_id = %s
                ORDER BY issued_at DESC, id DESC
                LIMIT 1
                """,
                (sid,),
            )
            latest = row[0] if row else {}
            generated.append((t, latest))
            print(
                f"OK  ID {sid} | {t.get('student_number')} | {name} | "
                f"code={latest.get('access_code')} | type={latest.get('access_type')} | expires={latest.get('expires_at')}"
            )
        except Exception as e:
            logger.error(f"Échec régénération ID {sid}: {e}")
            print(f"KO  ID {sid} | {t.get('student_number')} | {name} | erreur={e}")

    print("\nTerminé.")
    print(f"Codes régénérés: {len(generated)}/{len(targets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
