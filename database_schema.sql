-- Créer la base de données
CREATE DATABASE IF NOT EXISTS uor_university CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE uor_university;

-- Créer la table Faculty (Faculté)
CREATE TABLE IF NOT EXISTS faculty (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_code (code),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Créer la table Department (Département)
CREATE TABLE IF NOT EXISTS department (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    faculty_id INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_dept_per_faculty (code, faculty_id),
    INDEX idx_faculty (faculty_id),
    INDEX idx_code (code),
    INDEX idx_active (is_active),
    CONSTRAINT fk_department_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Créer la table Promotion (Promotion)
CREATE TABLE IF NOT EXISTS promotion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    year INT NOT NULL,
    description TEXT,
    department_id INT NOT NULL,
    fee_usd DECIMAL(10, 2) DEFAULT 0.00 COMMENT 'Frais académiques finaux de la promotion',
    threshold_amount DECIMAL(10, 2) DEFAULT 0.00 COMMENT 'Seuil minimum requis pour éligibilité',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_promo_per_dept (year, department_id),
    INDEX idx_department (department_id),
    INDEX idx_year (year),
    INDEX idx_active (is_active),
    CONSTRAINT fk_promotion_department FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Créer la table AcademicYear (Année académique)
CREATE TABLE IF NOT EXISTS academic_year (
    academic_year_id INT AUTO_INCREMENT PRIMARY KEY,
    year_name VARCHAR(50) NOT NULL UNIQUE,
    threshold_amount DECIMAL(15, 2) NOT NULL,
    final_fee DECIMAL(15, 2) NOT NULL,
    partial_valid_days INT DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Créer la table Student (Étudiant)
CREATE TABLE IF NOT EXISTS student (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_number VARCHAR(50) NOT NULL UNIQUE,
    firstname VARCHAR(255) NOT NULL,
    lastname VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone_number VARCHAR(20) DEFAULT NULL,
    passport_photo_path VARCHAR(512) DEFAULT NULL,
    passport_photo_blob LONGBLOB,
    promotion_id INT NOT NULL,
    academic_year_id INT DEFAULT NULL,
    password_hash VARCHAR(255) NOT NULL,
    face_encoding LONGBLOB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_student_number (student_number),
    INDEX idx_email (email),
    INDEX idx_promotion (promotion_id),
    INDEX idx_academic_year (academic_year_id),
    INDEX idx_active (is_active),
    INDEX idx_lastname (lastname),
    CONSTRAINT fk_student_promotion FOREIGN KEY (promotion_id) REFERENCES promotion(id) ON DELETE CASCADE,
    CONSTRAINT fk_student_academic_year FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Créer la table FinanceProfile (Profil Financier)
CREATE TABLE IF NOT EXISTS finance_profile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL UNIQUE,
    amount_paid DECIMAL(10, 2) DEFAULT 0.00,
    threshold_required DECIMAL(10, 2) NOT NULL,
    last_payment_date DATETIME,
    is_eligible BOOLEAN DEFAULT FALSE,
    academic_year_id INT DEFAULT NULL,
    access_code_issued_at TIMESTAMP NULL DEFAULT NULL,
    access_code_expires_at TIMESTAMP NULL DEFAULT NULL,
    access_code_type ENUM('full', 'partial') DEFAULT NULL,
    final_fee DECIMAL(15, 2) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_eligible (is_eligible),
    INDEX idx_amount (amount_paid),
    INDEX idx_finance_academic_year (academic_year_id),
    CONSTRAINT fk_finance_student FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
    CONSTRAINT fk_finance_academic_year FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Créer la table AccessLog (Journal d'Accès)
CREATE TABLE IF NOT EXISTS access_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    access_point VARCHAR(100),
    status ENUM('GRANTED', 'DENIED_PASSWORD', 'DENIED_FACE', 'DENIED_FINANCE', 'DENIED_MULTIPLE') NOT NULL,
    password_validated BOOLEAN DEFAULT FALSE,
    face_validated BOOLEAN DEFAULT FALSE,
    finance_validated BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_student (student_id),
    INDEX idx_status (status),
    INDEX idx_date (created_at),
    INDEX idx_access_point (access_point),
    CONSTRAINT fk_access_student FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insérer des données de test
INSERT INTO faculty (name, code, description) VALUES
('Faculté des Sciences', 'FS', 'Sciences et Technologies'),
('Faculté des Sciences de l''Ingénieur', 'FSI', 'Sciences et Ingénierie'),
('Faculté des Lettres', 'FL', 'Humanités et Lettres'),
('Faculté de Gestion', 'FG', 'Commerce et Management');

INSERT INTO department (name, code, faculty_id) VALUES
('Informatique', 'INFO', 1),
('Mathématiques', 'MATH', 1),
('Génie Informatique', 'G.I', 2),
('Génie Civil', 'G.C', 2),
('Français', 'FR', 3),
('Gestion', 'GEST', 4);

INSERT INTO promotion (name, year, department_id) VALUES
('L2 Informatique', 2024, 1),
('L3 Informatique', 2023, 1),
('L2 Mathématiques', 2024, 2),
('L3-LMD/G.I', 2023, 3),
('L2-LMD/G.I', 2024, 3),
('L2 Français', 2024, 5);

-- Note: Les mots de passe doivent être hashés avec bcrypt en application
-- Hash pour 'password123': $2b$12$... (généré par l'application)
INSERT INTO student (student_number, firstname, lastname, email, promotion_id, password_hash) VALUES
('STU001', 'Jean', 'Dupont', 'jean.dupont@university.edu', 1, '$2b$12$abcdefghijklmnopqrstuvwxyz'),
('STU002', 'Marie', 'Martin', 'marie.martin@university.edu', 1, '$2b$12$abcdefghijklmnopqrstuvwxyz'),
('STU003', 'Pierre', 'Bernard', 'pierre.bernard@university.edu', 2, '$2b$12$abcdefghijklmnopqrstuvwxyz'),
('STU004', 'Sophie', 'Garcia', 'sophie.garcia@university.edu', 3, '$2b$12$abcdefghijklmnopqrstuvwxyz'),
('STU005', 'Thomas', 'Rodriguez', 'thomas.rodriguez@university.edu', 1, '$2b$12$abcdefghijklmnopqrstuvwxyz');

INSERT INTO finance_profile (student_id, amount_paid, threshold_required, is_eligible) VALUES
(1, 500000, 500000, TRUE),
(2, 300000, 500000, FALSE),
(3, 500000, 500000, TRUE),
(4, 450000, 500000, FALSE),
(5, 250000, 500000, FALSE);
