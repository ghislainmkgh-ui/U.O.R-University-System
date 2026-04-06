#!/usr/bin/env python3
"""Audit access codes vs finance eligibility.

Usage:
    python scripts/audit_access_codes.py
"""
import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import DatabaseConnection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _date_only(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except Exception:
        return None


def main() -> int:
    db = DatabaseConnection()

    query = """
        SELECT
            s.id,
            s.student_number,
            s.firstname,
            s.lastname,
            s.academic_year_id,
            COALESCE(fp.amount_paid, 0) AS amount_paid,
            COALESCE(fp.threshold_required, 0) AS threshold_required,
            COALESCE(fp.is_eligible, 0) AS is_eligible,
            ach.access_code AS last_access_code,
            ach.access_type AS last_access_type,
            ach.expires_at AS last_expires_at,
            ach.issued_at AS last_issued_at
        FROM student s
        LEFT JOIN finance_profile fp
            ON fp.student_id = s.id
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
        ORDER BY s.id
    """

    try:
        rows = db.execute_query(query)
    except Exception as e:
        logger.error(f"Audit query failed: {e}", exc_info=True)
        return 1

    active_year_rows = db.execute_query(
        """
        SELECT academic_year_id
        FROM academic_year
        WHERE is_active = 1
        ORDER BY created_at DESC
        LIMIT 1
        """
    )
    active_year_id = active_year_rows[0]["academic_year_id"] if active_year_rows else None

    today = date.today()

    print("\n" + "=" * 128)
    print("AUDIT CODES D'ACCÈS (étudiant / finance / dernier code / expiration)")
    print("=" * 128)
    print(
        f"{'ID':>3} | {'N°':<10} | {'Nom':<24} | {'Payé':>10} | {'Seuil':>10} | {'Eligible':<8} | "
        f"{'Dernier code':<12} | {'Type':<7} | {'Expire':<10} | {'Statut code':<14}"
    )
    print("-" * 128)

    eligible_no_valid_code = []
    eligible_no_code = []
    expired_codes = []

    for r in rows:
        exp = _date_only(r.get("last_expires_at"))
        has_code = bool(r.get("last_access_code"))

        if not has_code:
            code_status = "AUCUN"
        elif (r.get("last_access_type") or "").lower() == "full":
            student_year_id = r.get("academic_year_id")
            if active_year_id is not None and student_year_id == active_year_id:
                code_status = "VALIDE"
            else:
                code_status = "EXPIRE"
        elif exp is None:
            code_status = "VALIDE"
        elif exp >= today:
            code_status = "VALIDE"
        else:
            code_status = "EXPIRE"

        eligible = bool(r.get("is_eligible"))

        if eligible and not has_code:
            eligible_no_code.append(r)
            eligible_no_valid_code.append(r)
        elif eligible and code_status != "VALIDE":
            eligible_no_valid_code.append(r)

        if has_code and code_status == "EXPIRE":
            expired_codes.append(r)

        name = f"{r.get('firstname', '')} {r.get('lastname', '')}".strip()
        print(
            f"{int(r.get('id')):>3} | "
            f"{str(r.get('student_number') or '-'):10.10} | "
            f"{name:24.24} | "
            f"{float(r.get('amount_paid') or 0):10.2f} | "
            f"{float(r.get('threshold_required') or 0):10.2f} | "
            f"{('OUI' if eligible else 'NON'):<8} | "
            f"{str(r.get('last_access_code') or '-'):12.12} | "
            f"{str(r.get('last_access_type') or '-'):7.7} | "
            f"{str(exp) if exp else '-':10.10} | "
            f"{code_status:<14}"
        )

    print("-" * 128)
    print(f"Total étudiants actifs: {len(rows)}")
    print(f"Codes expirés (dernier code): {len(expired_codes)}")
    print(f"Éligibles sans code: {len(eligible_no_code)}")
    print(f"Éligibles sans code valide: {len(eligible_no_valid_code)}")

    if eligible_no_valid_code:
        print("\n⚠ Étudiants éligibles sans code valide:")
        for r in eligible_no_valid_code:
            print(
                f"  - ID {r['id']} | {r.get('student_number')} | "
                f"{r.get('firstname')} {r.get('lastname')}"
            )

    print("\nAudit terminé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
