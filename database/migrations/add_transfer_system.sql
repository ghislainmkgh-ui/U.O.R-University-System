-- Migration: Système de Transfert Inter-Universitaire
-- Description: Ajoute les tables pour gérer les notes, documents et transferts d'étudiants
-- Date: 2026-02-25

USE uor_university;

-- Table pour les notes académiques des étudiants
CREATE TABLE IF NOT EXISTS academic_record (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    promotion_id INT NOT NULL,
    academic_year_id INT,
    course_name VARCHAR(255) NOT NULL COMMENT 'Nom du cours',
    course_code VARCHAR(50) COMMENT 'Code du cours',
    credits INT DEFAULT 0 COMMENT 'Crédits ECTS ou équivalent',
    grade DECIMAL(5, 2) COMMENT 'Note obtenue',
    grade_letter VARCHAR(5) COMMENT 'Note en lettre (A, B, C, etc.)',
    semester ENUM('1', '2', 'Annual') DEFAULT 'Annual',
    exam_date DATE COMMENT 'Date de l\'examen',
    professor_name VARCHAR(255) COMMENT 'Nom du professeur',
    status ENUM('PASSED', 'FAILED', 'IN_PROGRESS', 'VALIDATED') DEFAULT 'IN_PROGRESS',
    remarks TEXT COMMENT 'Remarques ou observations',
    is_transferred BOOLEAN DEFAULT FALSE COMMENT 'Provient d\'un transfert',
    source_university VARCHAR(255) COMMENT 'Université source si transféré',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_student (student_id),
    INDEX idx_promotion (promotion_id),
    INDEX idx_academic_year (academic_year_id),
    INDEX idx_status (status),
    INDEX idx_course_code (course_code),
    INDEX idx_transferred (is_transferred),
    CONSTRAINT fk_academic_record_student FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
    CONSTRAINT fk_academic_record_promotion FOREIGN KEY (promotion_id) REFERENCES promotion(id) ON DELETE CASCADE,
    CONSTRAINT fk_academic_record_academic_year FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table pour les documents et ouvrages des étudiants
CREATE TABLE IF NOT EXISTS student_document (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    document_type ENUM('BOOK', 'THESIS', 'REPORT', 'CERTIFICATE', 'DIPLOMA', 'OTHER') NOT NULL,
    title VARCHAR(500) NOT NULL COMMENT 'Titre du document ou ouvrage',
    description TEXT COMMENT 'Description détaillée',
    author VARCHAR(255) COMMENT 'Auteur (pour les ouvrages)',
    isbn VARCHAR(20) COMMENT 'ISBN pour les livres',
    category VARCHAR(100) COMMENT 'Catégorie (Sciences, Littérature, etc.)',
    file_path VARCHAR(1024) COMMENT 'Chemin du fichier numérique',
    file_blob LONGBLOB COMMENT 'Contenu du fichier',
    file_size_mb DECIMAL(10, 2) COMMENT 'Taille en MB',
    issue_date DATE COMMENT 'Date d\'émission/emprunt',
    return_date DATE COMMENT 'Date de retour prévue',
    status ENUM('ACTIVE', 'RETURNED', 'LOST', 'TRANSFERRED') DEFAULT 'ACTIVE',
    library_code VARCHAR(100) COMMENT 'Code bibliothèque',
    is_transferred BOOLEAN DEFAULT FALSE COMMENT 'A été transféré',
    source_university VARCHAR(255) COMMENT 'Université source si transféré',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_student (student_id),
    INDEX idx_type (document_type),
    INDEX idx_status (status),
    INDEX idx_isbn (isbn),
    INDEX idx_transferred (is_transferred),
    CONSTRAINT fk_student_document_student FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table pour l'historique des transferts
CREATE TABLE IF NOT EXISTS transfer_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transfer_code VARCHAR(100) NOT NULL UNIQUE COMMENT 'Code unique du transfert',
    student_id INT NOT NULL,
    transfer_type ENUM('OUTGOING', 'INCOMING') NOT NULL,
    source_university VARCHAR(255) COMMENT 'Université source',
    source_university_code VARCHAR(50) COMMENT 'Code de l\'université source',
    destination_university VARCHAR(255) COMMENT 'Université destination',
    destination_university_code VARCHAR(50) COMMENT 'Code de l\'université destination',
    transfer_date DATETIME NOT NULL,
    status ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED', 'REJECTED', 'CANCELLED') DEFAULT 'PENDING',
    
    -- Données statistiques sur le transfert
    records_count INT DEFAULT 0 COMMENT 'Nombre de notes transférées',
    documents_count INT DEFAULT 0 COMMENT 'Nombre de documents transférés',
    total_credits INT DEFAULT 0 COMMENT 'Total des crédits transférés',
    
    -- Métadonnées de sécurité
    initiated_by VARCHAR(255) COMMENT 'Utilisateur ayant initié le transfert',
    validated_by VARCHAR(255) COMMENT 'Utilisateur ayant validé',
    validation_date DATETIME COMMENT 'Date de validation',
    api_endpoint VARCHAR(512) COMMENT 'URL de l\'API utilisée',
    auth_token_hash VARCHAR(255) COMMENT 'Hash du token d\'authentification',
    
    -- Données du transfert (JSON)
    transfer_data_json LONGTEXT COMMENT 'Données complètes en JSON',
    response_json LONGTEXT COMMENT 'Réponse de l\'université destinataire',
    
    -- Audit
    error_message TEXT COMMENT 'Message d\'erreur si échec',
    notes TEXT COMMENT 'Notes ou remarques',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_student (student_id),
    INDEX idx_transfer_code (transfer_code),
    INDEX idx_type (transfer_type),
    INDEX idx_status (status),
    INDEX idx_transfer_date (transfer_date),
    INDEX idx_source_university (source_university_code),
    INDEX idx_destination_university (destination_university_code),
    CONSTRAINT fk_transfer_history_student FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table pour les demandes de transfert en attente
CREATE TABLE IF NOT EXISTS transfer_request (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_code VARCHAR(100) NOT NULL UNIQUE COMMENT 'Code unique de la demande',
    transfer_type ENUM('OUTGOING', 'INCOMING') NOT NULL,
    student_id INT COMMENT 'ID étudiant local (NULL pour INCOMING si pas encore créé)',
    
    -- Informations étudiant pour les transferts entrants
    external_student_number VARCHAR(100) COMMENT 'Numéro étudiant source',
    external_firstname VARCHAR(255),
    external_lastname VARCHAR(255),
    external_email VARCHAR(255),
    external_phone VARCHAR(20),
    
    -- Université source/destination
    source_university VARCHAR(255) NOT NULL,
    source_university_code VARCHAR(50),
    destination_university VARCHAR(255),
    destination_university_code VARCHAR(50),
    
    -- Faculté/Département/Promotion de destination
    target_faculty_id INT COMMENT 'Faculté de destination',
    target_department_id INT COMMENT 'Département de destination',
    target_promotion_id INT COMMENT 'Promotion de destination',
    
    -- Statut et workflow
    status ENUM('PENDING_REVIEW', 'APPROVED', 'REJECTED', 'COMPLETED') DEFAULT 'PENDING_REVIEW',
    requested_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_date DATETIME COMMENT 'Date de révision',
    reviewed_by VARCHAR(255) COMMENT 'Administrateur ayant révisé',
    
    -- Données reçues (pour INCOMING)
    received_data_json LONGTEXT COMMENT 'Données JSON reçues',
    
    -- Validation
    approval_notes TEXT COMMENT 'Notes d\'approbation ou de rejet',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_request_code (request_code),
    INDEX idx_type (transfer_type),
    INDEX idx_status (status),
    INDEX idx_student (student_id),
    INDEX idx_target_promotion (target_promotion_id),
    CONSTRAINT fk_transfer_request_student FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
    CONSTRAINT fk_transfer_request_faculty FOREIGN KEY (target_faculty_id) REFERENCES faculty(id) ON DELETE SET NULL,
    CONSTRAINT fk_transfer_request_department FOREIGN KEY (target_department_id) REFERENCES department(id) ON DELETE SET NULL,
    CONSTRAINT fk_transfer_request_promotion FOREIGN KEY (target_promotion_id) REFERENCES promotion(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table de configuration pour les universités partenaires
CREATE TABLE IF NOT EXISTS partner_university (
    id INT AUTO_INCREMENT PRIMARY KEY,
    university_name VARCHAR(255) NOT NULL UNIQUE,
    university_code VARCHAR(50) NOT NULL UNIQUE,
    country VARCHAR(100) NOT NULL,
    city VARCHAR(100),
    api_endpoint VARCHAR(512) COMMENT 'URL de l\'API de transfert',
    api_key_encrypted VARCHAR(512) COMMENT 'Clé API chiffrée',
    authentication_type ENUM('API_KEY', 'OAUTH', 'MUTUAL_TLS') DEFAULT 'API_KEY',
    is_active BOOLEAN DEFAULT TRUE,
    trust_level ENUM('VERIFIED', 'PENDING', 'BLOCKED') DEFAULT 'PENDING',
    last_communication DATETIME COMMENT 'Dernière communication réussie',
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_code (university_code),
    INDEX idx_active (is_active),
    INDEX idx_trust_level (trust_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insérer des données de test
INSERT INTO partner_university (university_name, university_code, country, city, trust_level, is_active) VALUES
('Université de Kinshasa', 'UNIKIN', 'RDC', 'Kinshasa', 'VERIFIED', TRUE),
('Université Protestante au Congo', 'UPC', 'RDC', 'Kinshasa', 'VERIFIED', TRUE),
('Université Pédagogique Nationale', 'UPN', 'RDC', 'Kinshasa', 'VERIFIED', TRUE),
('Institut Supérieur de Commerce', 'ISC', 'RDC', 'Kinshasa', 'PENDING', TRUE);

-- Vue pour obtenir le dossier académique complet d'un étudiant
CREATE OR REPLACE VIEW student_academic_profile AS
SELECT 
    s.id AS student_id,
    s.student_number,
    s.firstname,
    s.lastname,
    s.email,
    s.phone_number,
    f.name AS faculty_name,
    f.code AS faculty_code,
    d.name AS department_name,
    d.code AS department_code,
    p.name AS promotion_name,
    p.year AS promotion_year,
    COUNT(DISTINCT ar.id) AS total_courses,
    SUM(ar.credits) AS total_credits,
    AVG(ar.grade) AS average_grade,
    COUNT(DISTINCT sd.id) AS total_documents
FROM student s
LEFT JOIN promotion p ON s.promotion_id = p.id
LEFT JOIN department d ON p.department_id = d.id
LEFT JOIN faculty f ON d.faculty_id = f.id
LEFT JOIN academic_record ar ON s.id = ar.student_id
LEFT JOIN student_document sd ON s.id = sd.student_id
GROUP BY s.id, s.student_number, s.firstname, s.lastname, s.email, s.phone_number,
         f.name, f.code, d.name, d.code, p.name, p.year;

COMMIT;
