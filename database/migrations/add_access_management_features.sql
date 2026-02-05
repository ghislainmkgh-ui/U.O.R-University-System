-- Migration: Add access management features (password issuance, validity tracking, academic year)
-- Date: 2025

-- =====================================================
-- 1. MODIFY STUDENT TABLE - Add phone_number
-- =====================================================
ALTER TABLE student 
ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20) DEFAULT NULL AFTER email;

-- =====================================================
-- 2. CREATE ACADEMIC_YEAR TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS academic_year (
    academic_year_id INT AUTO_INCREMENT PRIMARY KEY,
    year_name VARCHAR(50) NOT NULL UNIQUE,  -- e.g., "2024-2025"
    threshold_amount DECIMAL(15, 2) NOT NULL,  -- Financial threshold for exam access
    final_fee DECIMAL(15, 2) NOT NULL,  -- Total fee for full year access
    partial_valid_days INT DEFAULT 30,  -- Days a partial payment code remains valid
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 3. CREATE EXAM_PERIOD TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS exam_period (
    exam_period_id INT AUTO_INCREMENT PRIMARY KEY,
    academic_year_id INT NOT NULL,
    period_name VARCHAR(100) NOT NULL,  -- e.g., "Session 1 - Janvier 2025"
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id) ON DELETE CASCADE,
    UNIQUE KEY unique_period (academic_year_id, period_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 4. MODIFY FINANCE_PROFILE TABLE - Add access code tracking
-- =====================================================
ALTER TABLE finance_profile 
ADD COLUMN IF NOT EXISTS academic_year_id INT DEFAULT NULL AFTER finance_id,
ADD COLUMN IF NOT EXISTS access_code_issued_at TIMESTAMP NULL DEFAULT NULL,
ADD COLUMN IF NOT EXISTS access_code_expires_at TIMESTAMP NULL DEFAULT NULL,
ADD COLUMN IF NOT EXISTS access_code_type ENUM('full', 'partial') DEFAULT NULL,
ADD COLUMN IF NOT EXISTS final_fee DECIMAL(15, 2) DEFAULT NULL,
ADD CONSTRAINT fk_finance_academic_year FOREIGN KEY (academic_year_id) 
    REFERENCES academic_year(academic_year_id) ON DELETE SET NULL;

-- =====================================================
-- 5. CREATE STUDENT_FACE_ENCODING TABLE (for multiple faces per student)
-- =====================================================
CREATE TABLE IF NOT EXISTS student_face_encoding (
    encoding_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    face_encoding LONGBLOB NOT NULL,  -- Numpy array serialized to bytes
    encoding_order TINYINT DEFAULT 1,  -- 1st, 2nd, or 3rd photo
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    UNIQUE KEY unique_encoding_order (student_id, encoding_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 6. INDEXES FOR PERFORMANCE
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_student_phone ON student(phone_number);
CREATE INDEX IF NOT EXISTS idx_finance_academic_year ON finance_profile(academic_year_id);
CREATE INDEX IF NOT EXISTS idx_finance_access_code_type ON finance_profile(access_code_type);
CREATE INDEX IF NOT EXISTS idx_exam_period_dates ON exam_period(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_face_encoding_student ON student_face_encoding(student_id);

-- =====================================================
-- 7. INSERT DEFAULT ACADEMIC YEAR (OPTIONAL)
-- =====================================================
-- Uncomment to create a default academic year:
-- INSERT INTO academic_year (year_name, threshold_amount, final_fee, partial_valid_days, is_active)
-- VALUES ('2024-2025', 100000.00, 200000.00, 30, TRUE);

-- =====================================================
-- 8. DATA INTEGRITY CHECKS
-- =====================================================
-- Ensure existing finance_profiles have access_code_type set if access_code exists
UPDATE finance_profile 
SET access_code_type = 'full' 
WHERE access_code IS NOT NULL 
  AND access_code != '' 
  AND access_code_type IS NULL 
  AND amount_paid >= threshold_required;

UPDATE finance_profile 
SET access_code_type = 'partial' 
WHERE access_code IS NOT NULL 
  AND access_code != '' 
  AND access_code_type IS NULL 
  AND amount_paid < threshold_required;

-- =====================================================
-- 9. MIGRATION NOTES
-- =====================================================
-- CRITICAL ACTIONS REQUIRED AFTER RUNNING THIS MIGRATION:
-- 1. Update config/settings.py with TWILIO credentials (WHATSAPP_ACCOUNT_SID, WHATSAPP_AUTH_TOKEN, WHATSAPP_FROM)
-- 2. Install Twilio: pip install twilio
-- 3. Create at least one academic year record with exam periods
-- 4. Re-generate access codes for existing eligible students (or run manual script)
-- 5. Populate student phone_number field for existing students
-- 6. Optionally migrate student.face_encoding to student_face_encoding table

-- =====================================================
-- 10. ROLLBACK SCRIPT (Use with caution)
-- =====================================================
/*
-- To rollback this migration (use with extreme caution - data will be lost):
ALTER TABLE finance_profile 
    DROP FOREIGN KEY fk_finance_academic_year,
    DROP COLUMN academic_year_id,
    DROP COLUMN access_code_issued_at,
    DROP COLUMN access_code_expires_at,
    DROP COLUMN access_code_type,
    DROP COLUMN final_fee;

ALTER TABLE student DROP COLUMN phone_number;

DROP TABLE IF EXISTS student_face_encoding;
DROP TABLE IF EXISTS exam_period;
DROP TABLE IF EXISTS academic_year;
*/
