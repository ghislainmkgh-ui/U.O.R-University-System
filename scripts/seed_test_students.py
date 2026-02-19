"""Seed 5 test students with required academic structure."""
from datetime import datetime
from decimal import Decimal
import mysql.connector as m
from config import settings as s
from core.security.password_hasher import PasswordHasher


def get_or_create(cur, table, where_clause, params, insert_sql, insert_params):
    cur.execute(f"SELECT id FROM {table} WHERE {where_clause}", params)
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(insert_sql, insert_params)
    cur.execute(f"SELECT id FROM {table} WHERE {where_clause}", params)
    row = cur.fetchone()
    return row[0] if row else None


def table_exists(cur, table_name: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
        (s.DB_NAME, table_name),
    )
    return bool(cur.fetchone()[0])


def get_columns(cur, table_name: str) -> set:
    cur.execute(
        "SELECT COLUMN_NAME FROM information_schema.columns WHERE table_schema=%s AND table_name=%s",
        (s.DB_NAME, table_name),
    )
    return {row[0] for row in cur.fetchall()}


def main() -> None:
    conn = m.connect(
        host=s.DB_HOST,
        user=s.DB_USER,
        password=s.DB_PASSWORD,
        database=s.DB_NAME,
        port=s.DB_PORT,
    )
    cur = conn.cursor()

    # Academic year
    if not table_exists(cur, "academic_year"):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS academic_year (
                academic_year_id INT AUTO_INCREMENT PRIMARY KEY,
                year_name VARCHAR(50) NOT NULL UNIQUE,
                threshold_amount DECIMAL(15, 2) NOT NULL,
                final_fee DECIMAL(15, 2) NOT NULL,
                partial_valid_days INT DEFAULT 30,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

    cur.execute("SELECT academic_year_id FROM academic_year WHERE year_name=%s", ("2024-2025",))
    row = cur.fetchone()
    if row:
        academic_year_id = row[0]
    else:
        cur.execute("UPDATE academic_year SET is_active=0")
        cur.execute(
            """
            INSERT INTO academic_year (year_name, threshold_amount, final_fee, partial_valid_days, is_active)
            VALUES (%s, %s, %s, %s, %s)
            """,
            ("2024-2025", "300", "500", 30, 1),
        )
        cur.execute("SELECT academic_year_id FROM academic_year WHERE year_name=%s", ("2024-2025",))
        academic_year_id = cur.fetchone()[0]

    # Faculty / Department / Promotion
    faculty_id = get_or_create(
        cur,
        "faculty",
        "code=%s",
        ("FSI",),
        "INSERT INTO faculty (name, code, is_active) VALUES (%s, %s, 1)",
        ("Faculté des Sciences de l'Ingénieur", "FSI"),
    )
    dept_id = get_or_create(
        cur,
        "department",
        "code=%s AND faculty_id=%s",
        ("G.I", faculty_id),
        "INSERT INTO department (name, code, faculty_id, is_active) VALUES (%s, %s, %s, 1)",
        ("Génie Informatique", "G.I", faculty_id),
    )
    promo_cols = get_columns(cur, "promotion")
    if "fee_usd" in promo_cols:
        promo_insert_sql = "INSERT INTO promotion (name, year, department_id, fee_usd, is_active) VALUES (%s, %s, %s, %s, 1)"
        promo_insert_params = ("L3-LMD/G.I", 2025, dept_id, "500")
    else:
        promo_insert_sql = "INSERT INTO promotion (name, year, department_id, is_active) VALUES (%s, %s, %s, 1)"
        promo_insert_params = ("L3-LMD/G.I", 2025, dept_id)

    promo_id = get_or_create(
        cur,
        "promotion",
        "name=%s AND department_id=%s",
        ("L3-LMD/G.I", dept_id),
        promo_insert_sql,
        promo_insert_params,
    )

    # Students
    base_students = [
        ("STU-T01", "MUMBERE", "KISONYA", "+243845046384", "ghislainmkgh@gmail.com"),
        ("STU-T02", "NORA", "MBUSA", "+243850000001", "nora.mbusa@example.com"),
        ("STU-T03", "ISAAC", "KALALA", "+243850000002", "isaac.kalala@example.com"),
        ("STU-T04", "GLORIA", "MABIKA", "+243850000003", "gloria.mabika@example.com"),
        ("STU-T05", "DENIS", "KASONGO", "+243850000004", "denis.kasongo@example.com"),
    ]

    password_hash = PasswordHasher.hash_password("123456")
    created = 0
    for student_number, firstname, lastname, phone, email in base_students:
        cur.execute("SELECT id FROM student WHERE student_number=%s", (student_number,))
        if cur.fetchone():
            continue
        student_cols = get_columns(cur, "student")
        insert_cols = ["student_number", "firstname", "lastname", "email", "promotion_id", "password_hash"]
        insert_vals = [student_number, firstname, lastname, email, promo_id, password_hash]

        if "phone_number" in student_cols:
            insert_cols.append("phone_number")
            insert_vals.append(phone)
        if "academic_year_id" in student_cols:
            insert_cols.append("academic_year_id")
            insert_vals.append(academic_year_id)
        if "is_active" in student_cols:
            insert_cols.append("is_active")
            insert_vals.append(1)
        if "created_at" in student_cols:
            insert_cols.append("created_at")
            insert_vals.append(datetime.now())
        if "updated_at" in student_cols:
            insert_cols.append("updated_at")
            insert_vals.append(datetime.now())

        cols_sql = ", ".join(insert_cols)
        placeholders = ", ".join(["%s"] * len(insert_cols))
        cur.execute(
            f"INSERT INTO student ({cols_sql}) VALUES ({placeholders})",
            tuple(insert_vals),
        )
        cur.execute("SELECT id FROM student WHERE student_number=%s", (student_number,))
        student_id = cur.fetchone()[0]

        # Finance profile
        amount_paid = Decimal("0")
        threshold_required = Decimal("300")
        final_fee = Decimal("500")
        finance_cols = get_columns(cur, "finance_profile")
        fin_cols = ["student_id", "amount_paid", "threshold_required", "is_eligible"]
        fin_vals = [student_id, str(amount_paid), str(threshold_required), 0]
        if "academic_year_id" in finance_cols:
            fin_cols.append("academic_year_id")
            fin_vals.append(academic_year_id)
        if "final_fee" in finance_cols:
            fin_cols.append("final_fee")
            fin_vals.append(str(final_fee))
        if "created_at" in finance_cols:
            fin_cols.append("created_at")
            fin_vals.append(datetime.now())
        if "updated_at" in finance_cols:
            fin_cols.append("updated_at")
            fin_vals.append(datetime.now())

        fin_cols_sql = ", ".join(fin_cols)
        fin_placeholders = ", ".join(["%s"] * len(fin_cols))
        cur.execute(
            f"INSERT INTO finance_profile ({fin_cols_sql}) VALUES ({fin_placeholders})",
            tuple(fin_vals),
        )
        created += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"OK: {created} étudiants de test insérés.")


if __name__ == "__main__":
    main()
