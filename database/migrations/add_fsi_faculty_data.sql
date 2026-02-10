-- Migration: Ajout de la Faculté des Sciences de l'Ingénieur (FSI) et données associées
-- Date: 2026-02-10
-- Description: Ajoute FSI, départements G.I et G.C, et promotions L3-LMD/G.I et L2-LMD/G.I

-- Ajouter la faculté FSI si elle n'existe pas
INSERT INTO faculty (name, code, description, is_active)
SELECT 'Faculté des Sciences de l''Ingénieur', 'FSI', 'Sciences et Ingénierie', 1
WHERE NOT EXISTS (SELECT 1 FROM faculty WHERE code = 'FSI');

-- Ajouter le département Génie Informatique
INSERT INTO department (name, code, faculty_id, is_active)
SELECT 'Génie Informatique', 'G.I', f.id, 1
FROM faculty f
WHERE f.code = 'FSI'
AND NOT EXISTS (SELECT 1 FROM department WHERE code = 'G.I');

-- Ajouter le département Génie Civil
INSERT INTO department (name, code, faculty_id, is_active)
SELECT 'Génie Civil', 'G.C', f.id, 1
FROM faculty f
WHERE f.code = 'FSI'
AND NOT EXISTS (SELECT 1 FROM department WHERE code = 'G.C');

-- Ajouter les promotions pour Génie Informatique
INSERT INTO promotion (name, year, department_id, is_active, fee_usd)
SELECT 'L3-LMD/G.I', 2023, d.id, 1, 1500.00
FROM department d
WHERE d.code = 'G.I'
AND NOT EXISTS (SELECT 1 FROM promotion WHERE name = 'L3-LMD/G.I' AND department_id = d.id);

INSERT INTO promotion (name, year, department_id, is_active, fee_usd)
SELECT 'L2-LMD/G.I', 2024, d.id, 1, 1200.00
FROM department d
WHERE d.code = 'G.I'
AND NOT EXISTS (SELECT 1 FROM promotion WHERE name = 'L2-LMD/G.I' AND department_id = d.id);

-- Afficher les résultats
SELECT 'Migration terminée' AS status;
SELECT * FROM faculty WHERE code = 'FSI';
SELECT d.* FROM department d JOIN faculty f ON d.faculty_id = f.id WHERE f.code = 'FSI';
SELECT p.* FROM promotion p JOIN department d ON p.department_id = d.id JOIN faculty f ON d.faculty_id = f.id WHERE f.code = 'FSI';
