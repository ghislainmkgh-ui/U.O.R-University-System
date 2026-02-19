#!/usr/bin/env python3
"""Verify students and their academic years"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import DatabaseConnection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = DatabaseConnection()

try:
    # Get student details with academic years
    query = """
        SELECT s.id, s.student_number, s.firstname, s.lastname, ay.year_name, ay.academic_year_id
        FROM student s
        LEFT JOIN academic_year ay ON s.academic_year_id = ay.academic_year_id
        ORDER BY s.id
    """
    results = db.execute_query(query)
    
    print("\n" + "="*80)
    print("STUDENTS WITH ACADEMIC YEARS")
    print("="*80)
    
    if results:
        for row in results:
            print(f"ID:{row['id']:2} | {row['student_number']:10} | {row['firstname']:12} {row['lastname']:12} | Year: {row['year_name']}")
    else:
        print("No students found!")
    
    print("\nDone!")
    
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    sys.exit(1)
