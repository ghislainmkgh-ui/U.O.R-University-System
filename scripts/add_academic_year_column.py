#!/usr/bin/env python3
"""Add academic_year_id column to student table if it doesn't exist"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import DatabaseConnection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = DatabaseConnection()

try:
    # Check if the column exists
    query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'student'
              AND COLUMN_NAME = 'academic_year_id'
    """
    results = db.execute_query(query)
    
    if not results:
        logger.info("Column academic_year_id does not exist. Adding it...")
        
        # Add the column
        alter_query = """
            ALTER TABLE student
            ADD COLUMN academic_year_id INT DEFAULT NULL,
            ADD CONSTRAINT fk_student_academic_year 
                FOREIGN KEY (academic_year_id) 
                REFERENCES academic_year(academic_year_id) 
                ON DELETE SET NULL,
            ADD INDEX idx_academic_year (academic_year_id)
        """
        db.execute_update(alter_query)
        logger.info("✓ Column academic_year_id added successfully")
    else:
        logger.info("✓ Column academic_year_id already exists")
        
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    sys.exit(1)

logger.info("Migration complete!")
