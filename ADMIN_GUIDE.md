# Guide Rapide - Administration du Système

## 🚀 Démarrage Rapide (Quick Start)

### Prérequis
- ✅ Migration SQL appliquée
- ✅ Python dependencies installées (`pip install -r requirements.txt`)
- ✅ MySQL en cours d'exécution
- ✅ Configuration Email/WhatsApp dans `config/settings.py`

---

## 📱 Configuration WhatsApp (Twilio)

### Étape 1: Créer Compte Twilio
1. Aller sur https://www.twilio.com/try-twilio
2. Créer compte gratuit (inclut $15 de crédit)
3. Vérifier votre email et numéro de téléphone

### Étape 2: Obtenir Credentials
1. Dans le dashboard Twilio, copier:
   - **Account SID** (commence par AC...)
   - **Auth Token** (cliquer "Show" pour voir)

### Étape 3: Activer WhatsApp Sandbox
1. Menu "Messaging" → "Try it out" → "Send a WhatsApp message"
2. Envoyer message au numéro Twilio depuis votre WhatsApp: `join [code]`
3. Copier le **WhatsApp Sandbox Number** (ex: +14155238886)

### Étape 4: Configurer Application
Éditer `config/settings.py`:
```python
WHATSAPP_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxx'  # Votre Account SID
WHATSAPP_AUTH_TOKEN = 'votre_auth_token'         # Votre Auth Token
WHATSAPP_FROM = '+14155238886'                    # Numéro sandbox Twilio
```

### Étape 5: Tester
```bash
python tests/test_notifications.py
```
Sélectionner option 2 (Test WhatsApp)

---

## 💼 Workflow Administrateur

### 1️⃣ Configurer l'Année Académique

#### Première Fois (après migration)
Le script `migration_helper.py` a déjà créé:
- Année: 2024-2025
- Seuil: 100,000 FC
- Frais finaux: 200,000 FC
- Validité partielle: 30 jours
- 3 Périodes d'examens

#### Vérifier Configuration
```python
from app.services.finance.academic_year_service import AcademicYearService

service = AcademicYearService()
year = service.get_active_year()
print(f"Année: {year['year_name']}")
print(f"Seuil: {year['threshold_amount']} FC")
print(f"Frais finaux: {year['final_fee']} FC")
```

#### Modifier Seuil (avec notification automatique)
```python
from app.services.finance.finance_service import FinanceService

service = FinanceService()
service.update_financial_thresholds(
    academic_year_id=1,
    new_threshold=150000.00,  # Nouveau seuil
    new_final_fee=250000.00   # Nouveaux frais finaux
)
# Tous les étudiants avec codes partiels seront notifiés automatiquement
```

---

### 2️⃣ Inscrire un Nouvel Étudiant

#### Via Interface (Recommandé)
1. Lancer application: `python main.py`
2. Connexion admin
3. Cliquer "Étudiants" → "+Ajouter Étudiant"
4. Remplir formulaire:
   - Matricule (unique)
   - Nom, prénom
   - Email (pour notifications)
   - **Téléphone** (format: +243XXXXXXXXX)
   - Faculté, promotion
5. Cliquer "📷 Sélectionner Photo Faciale"
6. Choisir photo claire du visage (face caméra, bien éclairé)
7. Cliquer "Enregistrer"

**Résultat**: 
- Encodage facial sauvegardé
- Finance profile créé (lié à année académique)
- Étudiant visible dans liste

#### Via Python (Script)
```python
from app.services.auth.authentication_service import AuthenticationService

service = AuthenticationService()
student_id = service.register_student_with_face(
    student_number="2024001",
    firstname="Jean",
    lastname="Dupont",
    email="jean.dupont@example.com",
    phone_number="+243123456789",
    faculty="Informatique",
    promotion="L1",
    photo_path="path/to/photo.jpg"
)
print(f"Étudiant créé avec ID: {student_id}")
```

---

### 3️⃣ Enregistrer un Paiement

#### Via Interface (Recommandé)
1. Page "Finance"
2. Trouver étudiant dans liste
3. Cliquer "Enregistrer paiement"
4. Entrer montant et méthode
5. Confirmer

**Automatique si seuil atteint**:
- Code 6 chiffres généré
- Type déterminé:
  - **Full** (vert): si montant ≥ frais finaux → valide toute l'année
  - **Partial** (orange): si seuil ≤ montant < frais finaux → valide 30 jours
- Notifications envoyées (Email + WhatsApp)
- Étudiant reçoit son code

#### Via Python
```python
from app.services.finance.finance_service import FinanceService

service = FinanceService()
service.record_payment(
    student_id=1,
    amount=100000.00,  # Montant en FC
    payment_method="Cash"
)
# Si seuil atteint → code généré et envoyé automatiquement
```

---

### 4️⃣ Consulter les Codes d'Accès

#### Requête SQL Directe
```sql
-- Voir tous les codes actifs
SELECT 
    s.student_number,
    s.firstname,
    s.lastname,
    fp.access_code_type,
    fp.access_code_issued_at,
    fp.access_code_expires_at
FROM student s
JOIN finance_profile fp ON s.student_id = fp.student_id
WHERE fp.is_eligible = TRUE
  AND (
    (fp.access_code_type = 'full') OR
    (fp.access_code_type = 'partial' AND fp.access_code_expires_at > NOW())
  );
```

#### Via Dashboard
Page "Finance" → Section "Codes d'Accès Actifs"

---

### 5️⃣ Gérer les Périodes d'Examens

#### Ajouter Nouvelle Période
```python
from app.services.finance.academic_year_service import AcademicYearService
from datetime import datetime

service = AcademicYearService()
service.add_exam_period(
    academic_year_id=1,
    period_name="Session 4 - Décembre 2025",
    start_date=datetime(2025, 12, 1),
    end_date=datetime(2025, 12, 15)
)
```

#### Lister Périodes
```python
periods = service.get_exam_periods(academic_year_id=1)
for p in periods:
    print(f"{p['period_name']}: {p['start_date']} → {p['end_date']}")
```

---

### 6️⃣ Ajouter Numéros Téléphone (Étudiants Existants)

#### Mise à Jour SQL
```sql
-- Un par un
UPDATE student 
SET phone_number = '+243123456789' 
WHERE student_id = 1;

-- Importation CSV (après préparation fichier)
LOAD DATA INFILE 'student_phones.csv'
INTO TABLE student
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(student_id, phone_number);
```

#### Via Python (Batch)
```python
from core.database.connection import DatabaseConnection

db = DatabaseConnection()
connection = db.get_connection()
cursor = connection.cursor()

# Liste des étudiants avec téléphones
students_phones = [
    (1, '+243123456789'),
    (2, '+243987654321'),
    # ...
]

for student_id, phone in students_phones:
    cursor.execute(
        "UPDATE student SET phone_number = %s WHERE student_id = %s",
        (phone, student_id)
    )

connection.commit()
cursor.close()
db.return_connection(connection)
```

---

## 🔍 Monitoring et Maintenance

### Vérifier Logs
```bash
# Logs application (erreurs générales)
tail -f logs/application.log

# Logs accès terminal
tail -f logs/access.log
```

### Statistiques Codes d'Accès
```sql
-- Compter par type
SELECT 
    access_code_type,
    COUNT(*) as nombre,
    SUM(CASE WHEN access_code_expires_at > NOW() THEN 1 ELSE 0 END) as actifs
FROM finance_profile
WHERE access_code IS NOT NULL
GROUP BY access_code_type;
```

### Codes Expirés (à renouveler)
```sql
-- Trouver codes partiels expirés
SELECT 
    s.student_number,
    s.firstname,
    s.lastname,
    s.email,
    s.phone_number,
    fp.access_code_expires_at
FROM student s
JOIN finance_profile fp ON s.student_id = fp.student_id
WHERE fp.access_code_type = 'partial'
  AND fp.access_code_expires_at < NOW()
ORDER BY fp.access_code_expires_at DESC;
```

---

## ⚠️ Gestion des Erreurs Communes

### Notification Email Échoue
**Symptôme**: Logs montrent "Error sending email"

**Solutions**:
1. Vérifier `EMAIL_ADDRESS` et `EMAIL_PASSWORD` dans config
2. Si Gmail: Activer "App Passwords" (pas le mot de passe normal)
   - https://myaccount.google.com/apppasswords
3. Vérifier connexion Internet
4. Tester: `python tests/test_notifications.py` → Option 1

### Notification WhatsApp Échoue
**Symptôme**: "WhatsApp service not configured" ou "Error sending WhatsApp"

**Solutions**:
1. Vérifier credentials Twilio dans config
2. Si sandbox: Vérifier que destinataire a rejoint sandbox (envoyé `join [code]`)
3. Vérifier format numéro: doit commencer par `+` (ex: +243123456789)
4. Vérifier crédit Twilio: https://console.twilio.com/
5. Tester: `python tests/test_notifications.py` → Option 2

### Code Non Généré Après Paiement
**Symptôme**: Étudiant paie seuil mais ne reçoit pas code

**Vérifications**:
```python
# 1. Vérifier finance_profile
SELECT amount_paid, threshold_required, is_eligible, access_code 
FROM finance_profile 
WHERE student_id = ?;

# 2. Vérifier année académique existe
SELECT * FROM academic_year WHERE is_active = TRUE;

# 3. Vérifier email/téléphone
SELECT email, phone_number FROM student WHERE student_id = ?;
```

**Forcer génération**:
```python
from app.services.finance.finance_service import FinanceService

service = FinanceService()
# Réenregistrer paiement trigger
service.record_payment(student_id=1, amount=0.01, payment_method="Adjustment")
```

### Reconnaissance Faciale Échoue
**Symptôme**: "Visage non reconnu" même avec bon étudiant

**Solutions**:
1. Vérifier qualité photo originale (éclairage, angle, résolution)
2. Recapturer 3 photos différentes (angles légèrement différents)
3. Nettoyer lentille caméra terminal
4. Ajuster seuil tolérance (0.6 par défaut):
```python
# Dans AccessController
if face_recognition.compare_faces([stored_encoding], input_encoding, tolerance=0.5)[0]:
    # Plus strict: 0.4-0.5
    # Plus permissif: 0.7-0.8
```

---

## 📞 Support Technique

### Contacts Urgents
- **Admin Système**: [votre_email@example.com]
- **Support Technique**: [support@example.com]
- **Twilio Support**: https://support.twilio.com/

### Ressources
- Documentation complète: `IMPLEMENTATION_SUMMARY.md`
- Guide migration: `database/migrations/README.md`
- Tests automatisés: `tests/test_notifications.py`
- Logs: `logs/application.log`

### Backup Réguliers
```bash
# Backup quotidien recommandé
mysqldump -u root -p database_name > backup_$(date +%Y%m%d).sql
```

---

## ✅ Checklist Journalière Admin

- [ ] Vérifier logs d'erreurs (`logs/application.log`)
- [ ] Consulter dashboard statistiques (Total étudiants, Éligibles, Revenus)
- [ ] Vérifier codes expirés (requête SQL ci-dessus)
- [ ] Traiter demandes inscription (si file d'attente)
- [ ] Vérifier notifications envoyées (Email + WhatsApp)
- [ ] Backup base de données (si jour prévu)

---

**Version**: 2.0  
**Dernière mise à jour**: 2025  
**Pour assistance**: Consulter `IMPLEMENTATION_SUMMARY.md` ou contacter l'équipe technique
