#!/usr/bin/env python3
"""Update existing students with academic_year_id"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import DatabaseConnection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = DatabaseConnection()

try:
    # Get the active academic year
    query = "SELECT academic_year_id FROM academic_year WHERE is_active = 1 LIMIT 1"
    results = db.execute_query(query)
    
    if not results:
        logger.error("No active academic year found. Create one first.")
        sys.exit(1)
    
    academic_year_id = results[0]['academic_year_id']
    logger.info(f"Found active academic year: {academic_year_id}")
    
    # Update students without academic_year_id
    update_query = """
        UPDATE student
        SET academic_year_id = %s
        WHERE academic_year_id IS NULL
    """
    db.execute_update(update_query, (academic_year_id,))
    
    # Check how many were updated
    count_query = "SELECT COUNT(*) as count FROM student WHERE academic_year_id = %s"
    count_results = db.execute_query(count_query, (academic_year_id,))
    
    if count_results:
        count = count_results[0]['count']
        logger.info(f"✓ Updated students: {count} students now have academic_year_id = {academic_year_id}")
    
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    sys.exit(1)

logger.info("Update complete!")
