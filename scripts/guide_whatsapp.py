"""Guide complet pour corriger WhatsApp Twilio"""

print("=" * 70)
print("🔧 CORRECTION WHATSAPP - GUIDE ÉTAPE PAR ÉTAPE")
print("=" * 70)

print("""
Le problème: Token d'authentification Twilio invalide ou expiré
Erreur actuelle: "Unable to create record: Authenticate"

╔════════════════════════════════════════════════════════════════════╗
║                    ÉTAPE 1: OBTENIR UN NOUVEAU TOKEN               ║
╚════════════════════════════════════════════════════════════════════╝

1. Va sur: https://console.twilio.com/
2. Connecte-toi avec tes identifiants Twilio
3. Tu verras le Dashboard principal

4. Cherche "Account Info" (en haut à droite ou dans le menu)
   Tu verras:
   • Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   • Auth Token: [masqué] avec un bouton "Show"

5. Clique sur "Show" pour révéler le token
6. COPIE le token (32 caractères, ex: d41d8cd98f00b204e9800998ecf8427e)

╔════════════════════════════════════════════════════════════════════╗
║              ÉTAPE 2: METTRE À JOUR LE FICHIER .env                ║
╚════════════════════════════════════════════════════════════════════╝

1. Ouvre le fichier: E:\\SECRET FILES\\MY_TFC\\.env
2. Cherche la ligne: TWILIO_AUTH_TOKEN=CVFBWQ4YH3EGDJVA4P4ZW4R7
3. Remplace par: TWILIO_AUTH_TOKEN=<ton_nouveau_token>

Exemple:
AVANT: TWILIO_AUTH_TOKEN=CVFBWQ4YH3EGDJVA4P4ZW4R7
APRÈS: TWILIO_AUTH_TOKEN=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

⚠️  IMPORTANT: Pas de guillemets, pas d'espaces!

╔════════════════════════════════════════════════════════════════════╗
║         ÉTAPE 3: REJOINDRE LE SANDBOX WHATSAPP (OBLIGATOIRE)      ║
╚════════════════════════════════════════════════════════════════════╝

Le Sandbox Twilio est GRATUIT mais nécessite que chaque personne s'inscrive:

1. Va sur: https://console.twilio.com/develop/sms/try-it-out/whatsapp-learn

2. Tu verras un message comme:
   "To use the Sandbox, send 'join <code>' to +14155238886"
   Exemple: "join coffee-piano"

3. Sur ton téléphone WhatsApp:
   • Ajoute le contact: +14155238886 (Twilio Sandbox)
   • Envoie le message: join <ton-code>
   
4. Tu recevras un message de confirmation:
   "You are all set! The sandbox is ready to use with your WhatsApp!"

5. IMPORTANT: Chaque étudiant devra faire la même chose pour recevoir des messages!

╔════════════════════════════════════════════════════════════════════╗
║                   ÉTAPE 4: TESTER LA CONNEXION                     ║
╚════════════════════════════════════════════════════════════════════╝

Après avoir mis à jour le token et rejoint le sandbox:

1. Ouvre PowerShell/Terminal
2. Exécute:
   cd "E:\\SECRET FILES\\MY_TFC"
   .venv\\Scripts\\python.exe scripts\\test_whatsapp.py

3. Entre ton numéro au format international: +243XXXXXXXXX
4. Tu devrais recevoir un message WhatsApp de test!

╔════════════════════════════════════════════════════════════════════╗
║                    ALTERNATIVE: EMAIL UNIQUEMENT                   ║
╚════════════════════════════════════════════════════════════════════╝

Si WhatsApp est trop compliqué:
• Les emails fonctionnent déjà parfaitement
• Aucune configuration supplémentaire nécessaire
• Gratuit et illimité
• Tu peux laisser WhatsApp vide dans .env

Pour désactiver WhatsApp:
1. Ouvre .env
2. Laisse vides:
   TWILIO_ACCOUNT_SID=
   TWILIO_AUTH_TOKEN=
   TWILIO_WHATSAPP_FROM=

╔════════════════════════════════════════════════════════════════════╗
║                   PASSAGE EN PRODUCTION (PAYANT)                   ║
╚════════════════════════════════════════════════════════════════════╝

Pour envoyer à tous sans que les étudiants rejoignent le sandbox:

1. Upgrader vers compte Twilio payant (~$20/mois)
2. Acheter un numéro WhatsApp Business
3. Soumettre tes templates de messages pour approbation Meta
4. Attendre l'approbation (2-5 jours)

Prix estimé:
• Compte Twilio: $20/mois
• Messages WhatsApp: $0.005 - $0.01 par message
• 1000 messages/mois ≈ $30/mois total

╔════════════════════════════════════════════════════════════════════╗
║                          DÉPANNAGE                                 ║
╚════════════════════════════════════════════════════════════════════╝

Erreur: "Authenticate"
→ Token invalide, renouvelle-le (Étape 1)

Erreur: "Destination number not in sandbox"
→ L'étudiant n'a pas rejoint le sandbox (Étape 3)

Erreur: "Message body is required"
→ Problème de code (contact support)

Aucun message reçu:
→ Vérifie que tu as rejoint le sandbox
→ Vérifie le format du numéro: +243... (pas d'espaces)
→ Attends 1-2 minutes (parfois lent)

╔════════════════════════════════════════════════════════════════════╗
║                         PROCHAINES ÉTAPES                          ║
╚════════════════════════════════════════════════════════════════════╝

1. Va sur https://console.twilio.com/ → Copie le nouveau token
2. Mets à jour .env avec le nouveau token
3. Rejoins le sandbox WhatsApp depuis ton téléphone
4. Exécute: python scripts/test_whatsapp.py
5. Si ça marche, teste en ajoutant un étudiant dans l'app!

Pour toute question, consulte:
• Documentation Twilio: https://www.twilio.com/docs/whatsapp
• Support: https://support.twilio.com/

""")

print("=" * 70)
input("\nAppuie sur Entrée pour fermer...")
