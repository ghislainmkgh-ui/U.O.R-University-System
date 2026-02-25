# 🔄 Système de Transfert Inter-Universitaire - Guide de Test

## 📋 Prérequis

Avant de tester le système, assurez-vous que :

1. ✅ La migration de base de données a été exécutée :
   ```bash
   python database/run_transfer_migration.py
   ```

2. ✅ Vous avez des étudiants dans la base de données avec des notes académiques

3. ✅ Le logiciel U.O.R est lancé et fonctionnel

## 🧪 Tests de l'Interface Utilisateur

### Test 1 : Accès à l'interface de transferts

1. Lancez l'application :
   ```bash
   python main.py
   ```

2. Connectez-vous avec un compte administrateur

3. Dans le menu latéral, cliquez sur l'icône 🔄 "Transferts"

4. **Résultat attendu** : Une page avec 3 onglets devrait s'afficher :
   - 📤 Transferts Sortants
   - 📥 Demandes Entrantes
   - 📜 Historique

### Test 2 : Créer un étudiant avec des notes (préparation)

Si vous n'avez pas encore d'étudiant avec des notes, créez-en un :

```sql
-- Créer un étudiant de test
INSERT INTO student (student_number, firstname, lastname, email, promotion_id, password_hash, is_active)
VALUES ('TEST001', 'Alice', 'Testeur', 'alice.test@uor.edu', 1, '$2b$12$test', TRUE);

-- Récupérer l'ID de l'étudiant créé
SET @student_id = LAST_INSERT_ID();

-- Ajouter quelques notes
INSERT INTO academic_record (student_id, promotion_id, course_name, course_code, credits, grade, grade_letter, semester, status)
VALUES 
    (@student_id, 1, 'Algorithmique Avancée', 'INF301', 6, 15.5, 'B+', '1', 'PASSED'),
    (@student_id, 1, 'Bases de Données', 'INF302', 6, 16.0, 'A-', '1', 'PASSED'),
    (@student_id, 1, 'Programmation Web', 'INF303', 4, 14.0, 'B', '2', 'PASSED'),
    (@student_id, 1, 'Intelligence Artificielle', 'INF401', 8, 17.5, 'A', '1', 'PASSED');

-- Ajouter quelques documents
INSERT INTO student_document (student_id, document_type, title, description, category, status)
VALUES 
    (@student_id, 'BOOK', 'Introduction à l\'IA', 'Livre de référence', 'Informatique', 'ACTIVE'),
    (@student_id, 'THESIS', 'Machine Learning et Big Data', 'Mémoire de fin d\'études', 'Informatique', 'ACTIVE');
```

### Test 3 : Générer un transfert sortant

1. Dans l'onglet "📤 Transferts Sortants" :

2. Sélectionnez l'étudiant "TEST001 - Alice Testeur" dans le menu déroulant

3. **Vérification** : Les informations de l'étudiant s'affichent :
   - Numéro étudiant
   - Nom complet
   - Email
   - Nombre de cours, crédits, moyenne
   - Nombre de documents

4. Sélectionnez une université de destination (ex: "Université de Kinshasa (UNIKIN)")

5. Laissez "Inclure les documents et ouvrages" coché

6. Ajoutez une note optionnelle, par exemple : "Transfert pour poursuite d'études en Master"

7. Cliquez sur "📤 Générer le Package de Transfert"

8. **Résultat attendu** :
   - Message de succès s'affiche
   - Code de transfert généré (format: UOR-XXX-YYYYMMDDHHMMSS)
   - Confirmation que les données ont été enregistrées

9. **Vérification en base de données** :
   ```sql
   SELECT * FROM transfer_history 
   WHERE student_id = @student_id 
   ORDER BY transfer_date DESC 
   LIMIT 1;
   ```

### Test 4 : Simuler un transfert entrant

1. Créez manuellement une demande de transfert entrante :

```sql
INSERT INTO transfer_request (
    request_code, transfer_type, external_student_number,
    external_firstname, external_lastname, external_email, external_phone,
    source_university, source_university_code,
    destination_university, destination_university_code,
    status, requested_date, received_data_json
) VALUES (
    'REQ-TEST123456',
    'INCOMING',
    'EXT001',
    'Bob',
    'Externe',
    'bob.externe@autre-universite.edu',
    '+243999999999',
    'Université de Kinshasa',
    'UNIKIN',
    'Université Officielle de Riba-Ulindi',
    'UOR',
    'PENDING_REVIEW',
    NOW(),
    '{
        "transfer_metadata": {
            "transfer_code": "UNIKIN-001-20260225",
            "source_university": "Université de Kinshasa",
            "source_university_code": "UNIKIN",
            "transfer_date": "2026-02-25T10:00:00",
            "certification": "Certified by UNIKIN"
        },
        "student_info": {
            "student_number": "EXT001",
            "firstname": "Bob",
            "lastname": "Externe",
            "email": "bob.externe@autre-universite.edu",
            "phone_number": "+243999999999",
            "faculty_name": "Informatique",
            "department_name": "Génie Logiciel",
            "promotion_name": "L2 Informatique"
        },
        "academic_records": {
            "total_courses": 10,
            "total_credits": 60,
            "average_grade": 13.5,
            "records": [
                {
                    "course_name": "Programmation Python",
                    "course_code": "PY101",
                    "credits": 6,
                    "grade": 14.0,
                    "grade_letter": "B",
                    "semester": "1",
                    "status": "PASSED"
                },
                {
                    "course_name": "Mathématiques Discrètes",
                    "course_code": "MATH201",
                    "credits": 6,
                    "grade": 13.0,
                    "grade_letter": "C+",
                    "semester": "1",
                    "status": "PASSED"
                }
            ]
        },
        "documents": {
            "total_documents": 1,
            "items": [
                {
                    "document_type": "CERTIFICATE",
                    "title": "Certificat de Scolarité",
                    "description": "2024-2025",
                    "category": "Administratif"
                }
            ]
        }
    }'
);
```

2. Dans l'application, allez dans l'onglet "📥 Demandes Entrantes"

3. **Résultat attendu** : Une carte s'affiche avec :
   - Nom : Bob Externe
   - Badge "⏳ EN ATTENTE"
   - Code de demande
   - Université source : Université de Kinshasa (UNIKIN)
   - Email et téléphone
   - Date de demande

4. Cliquez sur "👁️ Voir Détails"

5. **Vérification** : Une fenêtre popup s'ouvre avec toutes les données JSON formatées

6. Fermez la fenêtre de détails

### Test 5 : Approuver un transfert entrant

1. Dans l'onglet "📥 Demandes Entrantes", cliquez sur "✅ Approuver"

2. **Résultat attendu** : Une fenêtre de dialogue s'ouvre

3. Sélectionnez une promotion de destination (ex: "L2 Informatique - Informatique")

4. Ajoutez une note d'approbation : "Transfert approuvé pour intégration en L2"

5. Cliquez sur "✅ Approuver"

6. **Résultat attendu** :
   - Message de succès
   - ID du nouvel étudiant créé
   - Information sur le mot de passe temporaire
   - La demande disparaît de l'onglet "Demandes Entrantes"

7. **Vérification en base de données** :
```sql
-- Vérifier que l'étudiant a été créé
SELECT * FROM student WHERE firstname = 'Bob' AND lastname = 'Externe';

-- Vérifier que les notes ont été importées
SELECT * FROM academic_record WHERE student_id = (
    SELECT id FROM student WHERE firstname = 'Bob' AND lastname = 'Externe'
);

-- Vérifier que les notes sont marquées comme transférées
SELECT is_transferred, source_university FROM academic_record WHERE student_id = (
    SELECT id FROM student WHERE firstname = 'Bob' AND lastname = 'Externe'
);

-- Vérifier l'historique
SELECT * FROM transfer_history WHERE transfer_type = 'INCOMING' ORDER BY transfer_date DESC LIMIT 1;
```

### Test 6 : Consulter l'historique

1. Allez dans l'onglet "📜 Historique"

2. **Résultat attendu** : Un tableau s'affiche avec :
   - Header avec colonnes : Code, Étudiant, Type, Université, Date, Statut, Détails
   - Lignes pour chaque transfert
   - Couleurs différentes selon le statut (vert=COMPLETED, orange=PENDING, etc.)

3. Cliquez sur le bouton "👁️" d'une ligne

4. **Vérification** : Une fenêtre popup s'ouvre avec tous les détails du transfert

### Test 7 : Rejeter un transfert

1. Créez une nouvelle demande de transfert (répétez l'étape du Test 4)

2. Dans l'onglet "📥 Demandes Entrantes", cliquez sur "❌ Rejeter"

3. Entrez une raison : "Dossier incomplet - documents manquants"

4. Cliquez sur "❌ Rejeter"

5. **Résultat attendu** :
   - Message de succès
   - La demande disparaît de la liste

6. **Vérification en base de données** :
```sql
SELECT * FROM transfer_request WHERE status = 'REJECTED' ORDER BY reviewed_date DESC LIMIT 1;
```

## 🌐 Tests de l'API REST (Optionnel)

### Prérequis

1. Installer les dépendances :
   ```bash
   pip install -r api/requirements.txt
   ```

2. Lancer l'API :
   ```bash
   python api/transfer_api.py
   ```

### Test 8 : Health Check

```bash
curl http://localhost:5000/api/v1/health
```

**Résultat attendu** :
```json
{
  "status": "healthy",
  "service": "U.O.R Transfer API",
  "version": "v1",
  "timestamp": "2026-02-25T14:30:00"
}
```

### Test 9 : Obtenir un token d'authentification

```bash
curl -X POST http://localhost:5000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "university_code": "UNIKIN",
    "api_key": "test-key-123"
  }'
```

**Résultat attendu** :
```json
{
  "success": true,
  "token": "eyJ...",
  "expires_in": 86400,
  "token_type": "Bearer"
}
```

Copiez le token pour les tests suivants.

### Test 10 : Envoyer un package de transfert via API

```bash
curl -X POST http://localhost:5000/api/v1/transfer/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <VOTRE_TOKEN>" \
  -d '{
    "student_id": 1,
    "destination_university_code": "UNIKIN",
    "include_documents": true
  }'
```

### Test 11 : Recevoir un transfert via API

```bash
curl -X POST http://localhost:5000/api/v1/transfer/receive \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <VOTRE_TOKEN>" \
  -d @tests/sample_transfer.json
```

## ✅ Checklist Complète

- [ ] Migration de base de données exécutée
- [ ] Étudiant de test créé avec notes et documents
- [ ] Interface de transferts accessible
- [ ] Transfert sortant créé avec succès
- [ ] Demande entrante créée et visible
- [ ] Demande entrante approuvée avec succès
- [ ] Nouvel étudiant créé avec notes transférées
- [ ] Historique affiche les transferts
- [ ] Demande rejetée fonctionne
- [ ] API démarrée et accessible (optionnel)
- [ ] Health check API réussi (optionnel)
- [ ] Token d'authentification obtenu (optionnel)

## 🐛 Problèmes Courants et Solutions

### Problème 1 : Aucune université partenaire disponible

**Solution** : Les universités partenaires sont insérées automatiquement lors de la migration. Vérifiez :
```sql
SELECT * FROM partner_university;
```

Si vide, exécutez :
```sql
INSERT INTO partner_university (university_name, university_code, country, city, trust_level, is_active) VALUES
('Université de Kinshasa', 'UNIKIN', 'RDC', 'Kinshasa', 'VERIFIED', TRUE);
```

### Problème 2 : Erreur "Aucun étudiant disponible"

**Solution** : Créez au moins un étudiant (voir Test 2)

### Problème 3 : L'onglet ne s'affiche pas

**Solution** : Vérifiez les logs pour les erreurs. Assurez-vous que :
- Le service TransferService est importé correctement
- La base de données est accessible

### Problème 4 : Erreur lors de l'approbation

**Solution** : Vérifiez que :
- Une promotion existe dans la base de données
- Les données JSON sont valides
- La connexion à la base de données fonctionne

## 📊 Résultats Attendus

Après avoir complété tous les tests :

1. **Base de données** :
   - Au moins 1 transfert sortant dans `transfer_history`
   - Au moins 1 transfert entrant dans `transfer_history`
   - Au moins 1 nouvel étudiant créé via transfert
   - Notes marquées `is_transferred = TRUE`

2. **Interface** :
   - Historique affiche les transferts
   - Tous les onglets fonctionnent sans erreur
   - Les dialogues s'ouvrent et se ferment correctement

3. **Logs** :
   - Messages dans `logs/app.log` confirmant les opérations
   - Pas d'erreurs critiques

---

**Version du Guide** : 1.0  
**Date** : 25 février 2026  
**Prochaines Étapes** : Tester en environnement réel avec une vraie université partenaire
