# 🔧 Guide de Résolution - WhatsApp ne fonctionne plus

## 🔍 Problème Identifié

Votre instance Ultramsg a été **arrêtée pour non-paiement**.

**Message d'erreur :**
```
Your instance has been Stopped due to non-payment. 
You can activate this instance by extending your subscription.
```

---

## ✅ Solution 1 : Réactiver l'instance actuelle (Recommandé)

### Étape 1 : Se connecter à Ultramsg
1. Allez sur : https://api.ultramsg.com/
2. Cliquez sur **Login** en haut à droite
3. Connectez-vous avec vos identifiants

### Étape 2 : Vérifier le statut de votre instance
1. Dans le dashboard, cherchez votre instance : `instance162292`
2. Regardez le statut affiché

### Étape 3 : Réactiver votre abonnement
1. Cliquez sur **Subscriptions** ou **Billing**
2. Choisissez un plan :
   - **FREE** : 1000 messages/mois (gratuit pendant 1 mois)
   - **PRO** : Messages illimités (payant)
3. Activez votre abonnement
4. **Attendez 5 minutes** pour la synchronisation

### Étape 4 : Vérifier la connexion WhatsApp
1. Dans le dashboard, cliquez sur votre instance
2. Si le statut est "Disconnected", scannez le QR code avec WhatsApp
3. Attendez que le statut devienne "Connected" (vert)

### Étape 5 : Tester
```bash
python test_whatsapp.py
```

---

## 🆕 Solution 2 : Créer une nouvelle instance (Alternative)

### Étape 1 : Créer une nouvelle instance
1. Allez sur : https://api.ultramsg.com/
2. Connectez-vous (ou créez un compte)
3. Cliquez sur **Create Instance**
4. Notez le nom de votre nouvelle instance (ex: `instance234567`)

### Étape 2 : Connecter WhatsApp
1. Ouvrez WhatsApp sur votre téléphone
2. Allez dans **Paramètres** > **Appareils liés**
3. Cliquez sur **Lier un appareil**
4. Scannez le QR code affiché sur Ultramsg
5. Attendez la connexion (statut devient "Connected")

### Étape 3 : Récupérer les identifiants
1. Dans le dashboard Ultramsg, cliquez sur votre nouvelle instance
2. Copiez :
   - **Instance ID** (ex: `instance234567`)
   - **Token** (chaîne de caractères longue)

### Étape 4 : Mettre à jour le fichier .env

Ouvrez le fichier `.env` dans VS Code et modifiez :

```env
# Ultramsg WhatsApp API
ULTRAMSG_INSTANCE_ID=instance234567
ULTRAMSG_TOKEN=votre_nouveau_token_ici
```

⚠️ **Important** : Remplacez `instance234567` et `votre_nouveau_token_ici` par vos vraies valeurs !

### Étape 5 : Redémarrer l'application
```bash
python main.py
```

### Étape 6 : Tester WhatsApp
```bash
python test_whatsapp.py
```

---

## 🔄 Solution 3 : Utiliser Twilio (Alternative avancée)

Si Ultramsg ne fonctionne pas, vous pouvez utiliser Twilio WhatsApp :

### Avantages Twilio
- Plus fiable et professionnel
- Support technique 24/7
- Crédit gratuit de $15 pour tester

### Inconvénients
- Configuration plus complexe
- Nécessite vérification de numéro

### Configuration Twilio
1. Créez un compte sur : https://www.twilio.com/try-twilio
2. Suivez le guide dans `.env.example` (section WhatsApp Twilio)
3. Modifiez `notification_service.py` pour utiliser Twilio au lieu d'Ultramsg

---

## 🧪 Test de Diagnostic

Utilisez le script de test pour vérifier WhatsApp :

```bash
python test_whatsapp.py
```

### Résultats attendus

✅ **Si ça fonctionne :**
```
✅ Instance WhatsApp ACTIVE et CONNECTÉE
✅ MESSAGE ENVOYÉ AVEC SUCCÈS!
```

❌ **Si l'instance est déconnectée :**
```
❌ Instance WhatsApp NON CONNECTÉE
```
→ Scannez le QR code sur Ultramsg

❌ **Si l'instance est arrêtée :**
```
❌ Your instance has been Stopped due to non-payment
```
→ Suivez Solution 1 ou 2 ci-dessus

---

## 📞 Support

### Support Ultramsg
- Site : https://api.ultramsg.com/
- Documentation : https://docs.ultramsg.com/
- Email : support@ultramsg.com

### Support Application
- Vérifiez les logs dans le terminal lors de l'envoi de notifications
- Les logs WhatsApp montrent les détails des erreurs

---

## 📝 Checklist Rapide

- [ ] Instance Ultramsg active
- [ ] Abonnement valide (Free ou Pro)
- [ ] WhatsApp connecté (QR code scanné)
- [ ] Identifiants corrects dans `.env`
- [ ] Test réussi avec `python test_whatsapp.py`
- [ ] Notifications WhatsApp reçues dans l'application

---

## ⚡ Commandes Utiles

```bash
# Tester WhatsApp
python test_whatsapp.py

# Vérifier le fichier .env
Select-String -Path ".env" -Pattern "ULTRAMSG"

# Lancer l'application
python main.py

# Vérifier les logs d'erreur
# (Les logs s'affichent dans le terminal pendant l'exécution)
```

---

## 🎯 Résumé

**Le problème** : Instance Ultramsg arrêtée pour non-paiement

**La solution la plus rapide** :
1. Allez sur https://api.ultramsg.com/
2. Réactivez votre abonnement (plan gratuit disponible)
3. Attendez 5 minutes
4. Testez avec `python test_whatsapp.py`

**Durée estimée** : 5-10 minutes

---

*Guide créé le 01/03/2026*
