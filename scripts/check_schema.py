#!/usr/bin/env python3
"""Vérifier le schéma de la base de données"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import DatabaseConnection
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

db = DatabaseConnection()

# Check student table columns
print("=" * 60)
print("STUDENT TABLE COLUMNS")
print("=" * 60)
query = """
    SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'student'
    ORDER BY ORDINAL_POSITION
"""
results = db.execute_query(query)
if results:
    for row in results:
        print(f"{row['COLUMN_NAME']:25} | {row['COLUMN_TYPE']:20} | NULL={row['IS_NULLABLE']:3} | KEY={row['COLUMN_KEY']:3} | DEFAULT={row['COLUMN_DEFAULT']}")
else:
    print("No results!")

# Check academic_year table
print("\n" + "=" * 60)
print("ACADEMIC_YEAR TABLE COLUMNS")
print("=" * 60)
query = """
    SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'academic_year'
    ORDER BY ORDINAL_POSITION
"""
results = db.execute_query(query)
if results:
    for row in results:
        print(f"{row['COLUMN_NAME']:25} | {row['COLUMN_TYPE']:20} | NULL={row['IS_NULLABLE']:3} | KEY={row['COLUMN_KEY']:3} | DEFAULT={row['COLUMN_DEFAULT']}")
else:
    print("No results!")

# Test a student record
print("\n" + "=" * 60)
print("SAMPLE STUDENT RECORD")
print("=" * 60)
query = "SELECT id, student_number, firstname, lastname, academic_year_id FROM student LIMIT 1"
results = db.execute_query(query)
if results:
    for row in results:
        print(f"ID: {row['id']}")
        print(f"Student Number: {row['student_number']}")
        print(f"Firstname: {row['firstname']}")
        print(f"Lastname: {row['lastname']}")
        print(f"Academic Year ID: {row['academic_year_id']}")
else:
    print("No students found!")

print("\n" + "=" * 60)
print("ALL STUDENTS COUNT")
print("=" * 60)
query = "SELECT COUNT(*) as count FROM student"
results = db.execute_query(query)
if results:
    print(f"Total students: {results[0]['count']}")

print("\nDone!")
