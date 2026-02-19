-- Migration: Ajouter threshold_amount à la table promotion
-- Date: 2026-02-18
-- Description: Passer d'un système basé sur année académique à un système basé sur promotions
--              Chaque promotion aura ses propres frais finaux (fee_usd) et seuil (threshold_amount)

USE uor_university;

-- Ajouter la colonne threshold_amount à la table promotion
ALTER TABLE promotion 
ADD COLUMN threshold_amount DECIMAL(10, 2) DEFAULT 0.00 AFTER fee_usd,
ADD COLUMN description TEXT AFTER year;

-- Mettre à jour la colonne fee_usd pour avoir une valeur par défaut plus claire
ALTER TABLE promotion 
MODIFY COLUMN fee_usd DECIMAL(10, 2) DEFAULT 0.00 COMMENT 'Frais académiques finaux de la promotion';

-- Ajouter un commentaire sur threshold_amount
ALTER TABLE promotion 
MODIFY COLUMN threshold_amount DECIMAL(10, 2) DEFAULT 0.00 COMMENT 'Seuil minimum requis pour éligibilité';

-- Optionnel: Si vous avez une année académique active avec des valeurs par défaut,
-- vous pouvez pré-remplir les promotions existantes avec ces valeurs
-- Décommentez et adaptez selon vos besoins:

-- UPDATE promotion p
-- SET 
--     p.threshold_amount = (SELECT threshold_amount FROM academic_year WHERE is_active = 1 LIMIT 1),
--     p.fee_usd = (SELECT final_fee FROM academic_year WHERE is_active = 1 LIMIT 1)
-- WHERE p.threshold_amount = 0 OR p.fee_usd = 0;

-- Vérification
SELECT 
    p.name AS promotion_name,
    p.year,
    d.name AS department_name,
    f.name AS faculty_name,
    p.fee_usd AS frais_finaux,
    p.threshold_amount AS seuil,
    p.is_active
FROM promotion p
JOIN department d ON p.department_id = d.id
JOIN faculty f ON d.faculty_id = f.id
ORDER BY f.name, d.name, p.year;
