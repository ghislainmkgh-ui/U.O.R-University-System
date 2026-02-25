# Guide Complet du Système de Transfert Inter-Universitaire

## 📋 Vue d'Ensemble

Le système de transfert inter-universitaire de U.O.R permet l'échange sécurisé de données académiques entre établissements. Il facilite la mobilité étudiante en permettant le transfert des notes, documents et ouvrages.

### 🎯 Fonctionnalités Principales

1. **Transferts Sortants** : Exporter les données d'un étudiant vers une autre université
2. **Transferts Entrants** : Recevoir et valider des données d'étudiants provenant d'autres universités
3. **Gestion des Universités Partenaires** : Configuration des établissements de confiance
4. **Historique Complet** : Audit trail de tous les transferts
5. **Sécurité** : Validation, authentification et traçabilité

## 🗄️ Architecture de Base de Données

### Tables Principales

#### 1. `academic_record`
Stocke les notes et résultats académiques des étudiants.

**Champs clés** :
- `course_name` : Nom du cours
- `credits` : Crédits ECTS ou équivalent
- `grade` : Note obtenue
- `status` : PASSED, FAILED, IN_PROGRESS, VALIDATED
- `is_transferred` : Indique si la note vient d'un transfert
- `source_university` : Université d'origine si transféré

#### 2. `student_document`
Gère les documents et ouvrages des étudiants.

**Types de documents** :
- BOOK : Livres empruntés
- THESIS : Mémoires et thèses
- REPORT : Rapports académiques
- CERTIFICATE : Certificats
- DIPLOMA : Diplômes
- OTHER : Autres documents

#### 3. `transfer_history`
Historique complet de tous les transferts.

**Informations stockées** :
- Code unique de transfert
- Type (OUTGOING/INCOMING)
- Universités source et destination
- Statistiques (nombre de notes, documents, crédits)
- Données JSON complètes
- Statut (PENDING, IN_PROGRESS, COMPLETED, REJECTED, CANCELLED)

#### 4. `transfer_request`
Demandes de transfert en attente de validation.

**Workflow** :
1. Réception de la demande → `PENDING_REVIEW`
2. Révision par l'administrateur → `APPROVED` ou `REJECTED`
3. Si approuvé, création de l'étudiant → `COMPLETED`

#### 5. `partner_university`
Configuration des universités partenaires de confiance.

**Niveaux de confiance** :
- `VERIFIED` : Université vérifiée, transferts automatiques possibles
- `PENDING` : En cours de vérification
- `BLOCKED` : Transferts bloqués

## 🔧 Utilisation du Système

### A. Initier un Transfert Sortant

**Étapes** :

1. **Accéder à l'interface** :
   - Cliquer sur l'icône 🔄 "Transferts" dans le menu latéral
   - Sélectionner l'onglet "📤 Transferts Sortants"

2. **Sélectionner l'étudiant** :
   - Choisir l'étudiant dans la liste déroulante
   - Les informations académiques s'affichent automatiquement

3. **Choisir la destination** :
   - Sélectionner l'université partenaire de destination

4. **Options** :
   - Cocher "Inclure les documents et ouvrages" si souhaité
   - Ajouter des notes optionnelles

5. **Générer le package** :
   - Cliquer sur "📤 Générer le Package de Transfert"
   - Un code de transfert unique est généré
   - Les données sont enregistrées dans `transfer_history`

**Format du Package** :
```json
{
  "transfer_metadata": {
    "transfer_code": "UOR-123-20260225143000",
    "source_university": "Université Officielle de Riba-Ulindi",
    "source_university_code": "UOR",
    "transfer_date": "2026-02-25T14:30:00",
    "certification": "Certified by U.O.R Academic Office"
  },
  "student_info": {
    "student_number": "STU001",
    "firstname": "Jean",
    "lastname": "Dupont",
    "email": "jean.dupont@uor.edu",
    "faculty": "Informatique",
    "department": "Génie Informatique",
    "promotion": "L3-LMD/G.I"
  },
  "academic_records": {
    "total_courses": 25,
    "total_credits": 150,
    "average_grade": 14.5,
    "records": [
      {
        "course_name": "Programmation Avancée",
        "course_code": "INF301",
        "credits": 6,
        "grade": 15.5,
        "grade_letter": "B+",
        "semester": "1",
        "status": "PASSED"
      }
    ]
  },
  "documents": {
    "total_documents": 3,
    "items": [
      {
        "document_type": "THESIS",
        "title": "Intelligence Artificielle et Big Data",
        "author": "Jean Dupont",
        "category": "Informatique"
      }
    ]
  }
}
```

### B. Recevoir un Transfert Entrant

**Étapes** :

1. **Réception automatique** :
   - L'université source envoie les données via API
   - Une demande est créée avec statut `PENDING_REVIEW`

2. **Révision de la demande** :
   - Accéder à l'onglet "📥 Demandes Entrantes"
   - Cliquer sur "👁️ Voir Détails" pour examiner les données

3. **Approbation** :
   - Cliquer sur "✅ Approuver"
   - Sélectionner la promotion de destination
   - Ajouter des notes d'approbation (optionnel)
   - Confirmer

4. **Résultat** :
   - Un nouvel étudiant est créé
   - Toutes les notes sont importées avec `is_transferred = TRUE`
   - Les documents sont importés
   - Un historique de transfert est créé
   - Mot de passe temporaire : `ChangeMe123!`

### C. Consulter l'Historique

**Tableau d'historique** :
- Code de transfert
- Étudiant concerné
- Type (Sortant/Entrant)
- Université partenaire
- Date
- Statut
- Bouton pour voir les détails complets

## 🔐 Sécurité et Confidentialité

### Données Transférées ✅
- Informations personnelles de l'étudiant
- Notes et résultats académiques
- Documents et ouvrages
- Parcours académique

### Données NON Transférées ❌
- **Paiements** : Aucune donnée financière n'est transférée
- **Mots de passe** : Les hashes de mots de passe ne sont jamais exportés
- **Encodages faciaux** : Les données biométriques restent locales
- **Photos de passeport** : Les images ne sont pas transférées (sauf si explicitement configuré)

## 📡 API de Communication Inter-Universitaire

### Endpoint de Réception

**POST /api/v1/transfer/receive**

**Headers** :
```
Content-Type: application/json
Authorization: Bearer {api_key}
X-University-Code: UNIKIN
```

**Corps de la requête** : Package JSON complet (voir format ci-dessus)

**Réponse** :
```json
{
  "success": true,
  "request_code": "REQ-A1B2C3D4E5F6",
  "message": "Demande de transfert enregistrée avec succès",
  "status": "PENDING_REVIEW"
}
```

### Endpoint d'Envoi

**POST /api/v1/transfer/send**

**Corps** :
```json
{
  "destination_university_code": "UNIKIN",
  "transfer_code": "UOR-123-20260225143000"
}
```

## 🧪 Tests et Validation

### Scénario de Test 1 : Transfert Sortant Simple

1. Créer un étudiant avec quelques notes
2. Initier un transfert vers "Université de Kinshasa"
3. Vérifier que le code de transfert est généré
4. Vérifier que l'enregistrement existe dans `transfer_history`
5. Vérifier que le statut est `PENDING`

### Scénario de Test 2 : Transfert Entrant Complet

1. Créer une demande manuellement dans `transfer_request`
2. Accéder à l'interface des demandes entrantes
3. Approuver la demande
4. Vérifier qu'un nouvel étudiant est créé
5. Vérifier que les notes sont importées avec `is_transferred = TRUE`
6. Vérifier que le statut de la demande est `COMPLETED`

### Scénario de Test 3 : Rejet de Transfert

1. Créer une demande de transfert entrante
2. Cliquer sur "❌ Rejeter"
3. Entrer une raison de rejet
4. Vérifier que le statut passe à `REJECTED`
5. Vérifier que la raison est enregistrée

## 📊 Rapports et Statistiques

### Requêtes Utiles

**Nombre de transferts par université** :
```sql
SELECT 
    destination_university,
    COUNT(*) as total_transfers,
    SUM(records_count) as total_records_transferred,
    SUM(total_credits) as total_credits_transferred
FROM transfer_history
WHERE transfer_type = 'OUTGOING'
GROUP BY destination_university
ORDER BY total_transfers DESC;
```

**Étudiants avec notes transférées** :
```sql
SELECT 
    s.student_number,
    s.firstname,
    s.lastname,
    COUNT(ar.id) as transferred_courses,
    SUM(ar.credits) as transferred_credits
FROM student s
JOIN academic_record ar ON s.id = ar.student_id
WHERE ar.is_transferred = TRUE
GROUP BY s.id;
```

## 🛠️ Maintenance

### Purge des Anciennes Demandes

```sql
-- Supprimer les demandes rejetées de plus de 6 mois
DELETE FROM transfer_request
WHERE status = 'REJECTED' 
  AND reviewed_date < DATE_SUB(NOW(), INTERVAL 6 MONTH);
```

### Vérification d'Intégrité

```sql
-- Vérifier que tous les transferts COMPLETED ont un étudiant associé
SELECT * FROM transfer_history
WHERE status = 'COMPLETED' 
  AND transfer_type = 'INCOMING'
  AND student_id IS NULL;
```

## 🚀 Évolutions Futures

### Phase 2 : API REST Complète
- Endpoints publics pour communication automatique
- Authentification OAuth 2.0
- Webhooks pour notifications

### Phase 3 : Blockchain
- Hash des transferts sur blockchain pour certification immuable
- Vérification de l'authenticité des diplômes

### Phase 4 : Intelligence Artificielle
- Validation automatique des équivalences de cours
- Détection de fraudes
- Recommandations de parcours

## 📞 Support

Pour toute question ou problème :
- Email : support@uor.edu.cd
- Documentation technique : `/docs/transfer-api.md`
- Logs : Consultez les fichiers dans `/logs/transfer_*.log`

## ⚖️ Conformité Légale

Ce système est conforme à :
- RGPD (Protection des données personnelles)
- Normes LMD (Système Licence-Master-Doctorat)
- Protocoles ECTS (European Credit Transfer System)
- Directives du Ministère de l'Enseignement Supérieur de la RDC

---

**Version** : 1.0  
**Date** : 25 février 2026  
**Auteur** : Équipe Technique U.O.R
