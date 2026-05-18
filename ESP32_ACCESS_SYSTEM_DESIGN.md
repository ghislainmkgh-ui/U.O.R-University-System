# ESP32 Access Control System Design

## Objectif

Créer un système d’accès à une salle d’examen avec contrôle strict :
- code valide
- reconnaissance faciale
- passage unique au niveau de l’entrée
- sortie gérée proprement
- accès des autorités séparé
- protection anti-fraude

Ce document propose l’architecture, les composants, le câblage, les règles physiques et les comportements à implémenter avant toute modification de code.

---

## 1. Architecture globale

### 1.1 Composants principaux

1. **ESP32 Dev Module** (base du contrôle)
2. **Clavier 4x4** pour la saisie du code
3. **LCD I2C 16x2** pour l’affichage des messages à l’usager
4. **Servo moteur** ou serrure électromécanique pour l’ouverture de la porte
5. **Deux capteurs ultrason HC-SR04** : un à l’extérieur et un à l’intérieur
6. **Capteur de porte magnétique (reed switch)** pour détecter porte ouverte/fermée
7. **Bouton poussoir intérieur** pour la sortie uniquement
8. **LED verte / rouge** pour signaler l’état access granted / denied
9. **Lecteur RFID / badge** pour l’accès des autorités
10. **Optionnel : barrière IR supplémentaire** pour renforcer encore la détection de plusieurs personnes

### 1.2 Pourquoi ces composants

- L’ESP32 gère le réseau, le clavier, l’affichage, le servo et les capteurs.
- Les deux ultrasons détectent l’ordre de passage : extérieur puis intérieur pour une entrée valide.
- Le capteur de porte permet de savoir si la porte est bien fermée et si une sortie est réalisée.
- Le bouton intérieur ne peut pas être utilisé pour accorder l’accès à quelqu’un à l’extérieur si le bouton est installé derrière la porte.
- La barrière IR peut encore améliorer la fiabilité contre le "tailgating", mais la base retenue est déjà `2 x HC-SR04`.

### 1.3 Composants Arduino Uno kit utilisables

Ton kit Arduino Uno est utile pour le prototype. Nous pouvons réutiliser ces composants avec l’ESP32 :
- `2 x HC-SR04` (ultrason extérieur + ultrason intérieur)
- `reed switch` magnétique pour la porte
- `bouton poussoir` pour la sortie intérieure
- `LED` rouge et verte
- `résistances` 10 kΩ et 20 kΩ pour le diviseur de tension
- `câbles jumper` et `breadboard`
- éventuellement `capteurs IR` ou transistors si disponibles

Le seul changement est que le contrôleur principal restera l’ESP32, mais les capteurs et boutons du kit Arduino Uno fonctionnent très bien avec lui.

---

## 2. Règles de fonctionnement proposées

### 2.1 Conditions d’accès

Un étudiant ne peut entrer que si :
- son `code` est validé par le serveur
- son `visage` est reconnu par le serveur
- la porte est actuellement `fermée`
- la salle est `libre`
- la détection de passage confirme un `unique entrant`

### 2.2 Sortie

- la sortie se fait par un `bouton intérieur`
- le bouton intérieur doit être installé à l’intérieur, au-delà de la porte
- le bouton ne doit pas ouvrir la porte pour un usager dehors
- le bouton intérieur ne peut être actif que si la salle est `occupée`
- la sortie doit être confirmée par le capteur de porte ou le capteur ultrason

### 2.3 Autorités

Il faut un mode séparé pour les autorités :
- accès par carte/badge RFID dédié
- lecteur RFID séparé installé à l’entrée
- vérification côté serveur pour autoriser l’accès des autorités
- le système doit loguer chaque accès des autorités
- le système peut tolérer un accès autorité même si la salle est occupée, mais avec mention d’alerte et log

### 2.4 Anti-fraude

- une fois l’accès accordé, la porte s’ouvre seulement pendant une courte fenêtre
- si plusieurs passages sont détectés, le système annule ou alerte
- aucune nouvelle entrée n’est autorisée tant que la sortie n’est pas complète
- le bouton intérieur ne doit pas servir à autoriser l’entrée extérieure
- garder un état logiciel `occupé` / `libre`

---

## 3. Capteurs et placement physique

### 3.1 Capteurs ultrason HC-SR04

- Alimentation : `5V` (avec conversion rouge/bleu pour ESP32)
- Ultrason extérieur : placé face à la zone d’entrée, à environ `20–30 cm` de l’ouverture côté extérieur
- Ultrason intérieur : placé côté intérieur, à environ `20–30 cm` après la porte
- Chaque Echo doit aller vers l’ESP32 via `diviseur de tension` (3.3V safe)
- Hauteur : `80–120 cm` du sol pour détecter le buste d’une personne
- Distance de détection utile : `100 mm à 400 mm`

**Pourquoi deux capteurs à 20–30 cm** ?
- le HC-SR04 est le plus fiable dans une courte distance devant la porte
- il évite les fausses détections sur des objets plus éloignés
- l’ordre extérieur → intérieur confirme une entrée
- l’ordre intérieur → extérieur confirme une sortie

### 3.2 Capteur de porte magnétique

- Montage : un aimant sur la porte, un capteur fixe sur le cadre
- Écart maximum : `<= 5 mm`
- Utilisation : détecter porte `fermée` / `ouverte`

### 3.3 Bouton poussoir intérieur

- Installer `à l’intérieur de la salle`
- À au moins `0,5 m` derrière la porte, de manière à ce qu’une personne dehors ne puisse pas l’atteindre
- Le bouton ne donne accès que pour `sortie`
- Il est conseillé de le rendre physiquement difficile d’accès depuis l’extérieur

### 3.4 Optionnel : barrière IR supplémentaire

Recommandé si tu veux limiter les fraudes plus fortement :
- deux capteurs infrarouges configurés en ``entrée`` / ``intérieur``

Cela permet de :
- confirmer encore mieux `1 personne entrant`
- détecter plus précisément `passage inverse`
- repérer plus vite `plusieurs personnes`

---

## 4. Schéma de comportement logiciel

### 4.1 États du système

1. `IDLE` : attente code à l’extérieur
2. `CODE_VALIDATION` : envoi du code au serveur
3. `FACE_VALIDATION` : envoi de la vérification faciale
4. `AWAIT_ENTRY_WINDOW` : accès autorisé, porte sur le point d’ouvrir
5. `PASSAGE_DETECTE` : l’utilisateur passe
6. `SALLE_OCCUPEE` : entrée bloquée, attente sortie
7. `EXIT_REQUESTED` : appui bouton intérieur
8. `SORTIE_CONFIRMEE` : retour à freed state
9. `AUTHORITY_MODE` : accès admin / autorités

### 4.2 Flux d’entrée recommandé

1. l’étudiant saisi son code sur le clavier
2. le système affiche `Vérification code...`
3. le serveur répond : `pending_face` ou `granted`
4. si code OK, le système affiche `Analyse visage...`
5. le serveur vérifie la biométrie faciale
6. si visage validé :
   - vérifier que la porte est `fermée`
   - vérifier que la zone d’entrée est libre (`ultrason`) 
   - ouvrir la porte
   - attendre un passage unique devant le capteur
   - fermer la porte dès que le passage est confirmé
   - changer l’état en `occupé`
7. si le code ou le visage échoue : accès refusé

### 4.3 Flux de sortie recommandé

1. l’utilisateur à l’intérieur appuie sur le bouton de sortie
2. le système vérifie l’état `occupé`
3. la porte s’ouvre pour sortie
4. le capteur de porte ou l’ultrason confirme que la personne a quitté
5. la porte se referme
6. l’état passe à `libre`
7. seulement après confirmation, un autre étudiant peut commencer la procédure d’entrée

### 4.4 Flux autorité recommandé

1. l’autorité présente sa carte/badge RFID devant le lecteur dédié
2. le serveur identifie le badge comme autorité
3. si autorité validée : accès autorisé
4. le système peut loguer `ACCESS AUTHORITY`
5. si l’autorité doit entrer alors que la salle est occupée, prévoir un état `override` et une alerte

---

## 5. Blocage du bouton intérieur pour l’accès extérieur

C’est une exigence essentielle :

- le bouton intérieur ne DOIT PAS être un moyen d’ouverture pour une personne dehors
- il doit être uniquement accessible depuis l’intérieur
- son seul rôle est `SORTIE`
- il ne doit jamais déclencher un nouvel accès extérieur
- sur le plan logiciel, il n’agit que si l’état du système est `occupé`

**Implémentation physique** :
- placer le bouton sur le mur intérieur de la salle, derrière la ligne de la porte
- si la porte est fermée, impossible de l’atteindre depuis l’extérieur
- si la porte est ouverte, la structure doit encore empêcher un utilisateur extérieur de l’actionner

---

## 6. Détails de câblage recommandés

### 6.1 Assignation des pins

| Fonction | Composant | Pin ESP32 proposé |
| --- | --- | --- |
| Servo porte | Servo / serrure | GPIO 4 |
| LCD I2C SDA | LCD I2C | GPIO 21 |
| LCD I2C SCL | LCD I2C | GPIO 22 |
| Keypad ligne 1 | Keypad | GPIO 13 |
| Keypad ligne 2 | Keypad | GPIO 12 |
| Keypad ligne 3 | Keypad | GPIO 14 |
| Keypad ligne 4 | Keypad | GPIO 27 |
| Keypad col 1 | Keypad | GPIO 26 |
| Keypad col 2 | Keypad | GPIO 25 |
| Keypad col 3 | Keypad | GPIO 33 |
| Keypad col 4 | Keypad | GPIO 32 |
| LED verte | LED | GPIO 2 |
| LED rouge | LED | GPIO 15 |
| HC-SR04 extérieur TRIG | Ultrason extérieur | GPIO 16 |
| HC-SR04 extérieur ECHO | Ultrason extérieur | GPIO 17 (via diviseur) |
| HC-SR04 intérieur TRIG | Ultrason intérieur | GPIO 18 |
| HC-SR04 intérieur ECHO | Ultrason intérieur | GPIO 19 (via diviseur) |
| Reed switch porte | Porte | GPIO 34 / entrée digitale |
| Bouton sortie | Sortie | GPIO 35 / entrée digitale |
| Lecteur RFID autorités | PN532 I2C recommandé | SDA GPIO 21, SCL GPIO 22, RSTO GPIO 5 optionnel |

Cette table suit le code `esp32_access_full_single_file.ino`. Les GPIO 18 et 19 sont réservés à l’ultrason intérieur. Il ne faut donc pas activer un lecteur MFRC522 SPI avec ces pins sans remapper le SPI.

### 6.2 Alimentation

- ESP32 : `5V` régulé ou via USB
- Servo : `5V` stable, alimentation séparée si possible
- HC-SR04 : `5V`
- LCD I2C : `5V`
- Reed switch et bouton : `3.3V logique`

### 6.3 Capteur ultrason et ESP32

- **Ne jamais connecter directement le signal Echo 5V au GPIO ESP32**
- utiliser un **diviseur de tension** ou un circuit logique 3.3V
- Exemple : 10 kΩ / 20 kΩ, soit la sortie ramenée à ~3.3V

### 6.4 Lecteur RFID et badges autorités

Pour l’accès autorités, utiliser un lecteur RFID compatible badge 13.56 MHz. Avec deux HC-SR04, le choix le plus propre est le **PN532 en I2C**, parce qu’il partage le bus SDA/SCL avec le LCD sans prendre les GPIO 18/19.

- Recommandé : **PN532 I2C**
  - SDA -> GPIO 21
  - SCL -> GPIO 22
  - RSTO -> GPIO 5
  - IRQ -> libre / non obligatoire
- Alternative possible : **MFRC522 SPI**, mais seulement si tu remappes SPI sur des pins libres avant d’activer `USE_RFID = 1`
  - ne pas utiliser GPIO 18 / GPIO 19
  - ne pas utiliser GPIO 4 si le servo reste sur GPIO 4
  - garder une table de pins unique dans le code et dans ce document

### 6.5 Câblage physique recommandé

- `ESP32 5V` -> `LCD 5V`, `HC-SR04 extérieur 5V`, `HC-SR04 intérieur 5V`, `PN532 5V`, `Servo 5V`
- `ESP32 GND` -> `LCD GND`, `HC-SR04 extérieur GND`, `HC-SR04 intérieur GND`, `PN532 GND`, `Servo GND`
- `ESP32 GPIO 21` -> `LCD SDA` + `PN532 SDA`
- `ESP32 GPIO 22` -> `LCD SCL` + `PN532 SCL`
- `ESP32 GPIO 13` -> `Keypad ligne 1`
- `ESP32 GPIO 12` -> `Keypad ligne 2`
- `ESP32 GPIO 14` -> `Keypad ligne 3`
- `ESP32 GPIO 27` -> `Keypad ligne 4`
- `ESP32 GPIO 26` -> `Keypad col 1`
- `ESP32 GPIO 25` -> `Keypad col 2`
- `ESP32 GPIO 33` -> `Keypad col 3`
- `ESP32 GPIO 32` -> `Keypad col 4`
- `ESP32 GPIO 4` -> `Servo porte`
- `ESP32 GPIO 2` -> `LED verte`
- `ESP32 GPIO 15` -> `LED rouge`
- `ESP32 GPIO 16` -> `HC-SR04 extérieur TRIG`
- `ESP32 GPIO 17` -> `HC-SR04 extérieur ECHO` (via diviseur 3.3V)
- `ESP32 GPIO 18` -> `HC-SR04 intérieur TRIG`
- `ESP32 GPIO 19` -> `HC-SR04 intérieur ECHO` (via diviseur 3.3V)
- `ESP32 GPIO 34` -> `Reed switch porte`
- `ESP32 GPIO 35` -> `Bouton sortie intérieur`
- `ESP32 GPIO 5` -> `PN532 RSTO` optionnel

> Le MFRC522 SPI n’est pas conseillé dans ce câblage final, car le SPI classique utiliserait souvent GPIO 18 et GPIO 19, déjà occupés par l’ultrason intérieur.

---

## 7. Distances et contraintes physiques

### 7.1 Position des ultrasons

- ultrason extérieur : `20–30 cm` avant la porte, orienté vers la zone d’entrée
- ultrason intérieur : `20–30 cm` après la porte, orienté vers la zone de sortie
- hauteur : `100 cm ± 20 cm` pour les deux capteurs
- utiliser un support rigide pour éviter les mouvements
- angle : chaque capteur doit être bien centré sur sa zone de passage

### 7.2 Zones de détection

- seuil de présence : `<= 200 mm` (20 cm) devant chaque capteur
- zone libre : distance supérieure à `300 mm` (30 cm) sur les deux capteurs avant l’ouverture
- entrée valide : détection extérieure puis détection intérieure
- sortie valide : détection intérieure puis détection extérieure
- si un objet se trouve à moins de `100 mm`, c’est trop proche et peut provoquer de mauvais calculs
- si le capteur est trop loin (> 400 mm), le signal devient moins stable

### 7.3 Position du bouton intérieur

- distance minimale du bord de porte : `50 cm`
- idéalement plus de `70 cm` à l’intérieur pour éviter toute manipulation depuis l’extérieur
- hauteur bouton : `100–120 cm`

### 7.4 Position du capteur de porte magnétique

- aimant et contact alignés
- écart max `5 mm`
- montage sur charnière / cadre de porte

---

## 8. Détection d’un passage unique

### 8.1 Détection avec deux HC-SR04

- ouvre la porte
- commence à lire les deux distances
- pour une entrée, le capteur extérieur doit détecter avant le capteur intérieur
- pour une sortie, le capteur intérieur doit détecter avant le capteur extérieur
- la deuxième détection doit arriver dans la fenêtre prévue, sinon le passage est considéré incomplet
- si les deux capteurs détectent en même temps ou plusieurs fois dans le même cycle, considérer la situation comme `fraude possible`

### 8.2 Règles de décision serveur / ESP32

- `extérieur -> intérieur` : envoyer `entry_confirmed`
- `intérieur -> extérieur` : envoyer `exit_confirmed`
- aucune deuxième détection : envoyer `entry_failed` ou `exit_failed`
- détection multiple ou incohérente : envoyer `passage_invalid`
- le serveur ne passe en `occupied` qu’après `entry_confirmed`
- le serveur ne repasse en `free` qu’après `exit_confirmed`

> Cette décision à deux capteurs est retenue pour le projet. Une barrière IR peut être ajoutée plus tard, mais elle devient un renfort, pas la base du système.

---

## 9. Flux anti-fraude recommandé

### 9.1 Conditions d’ouverture

- code valide
- visage validé
- salle libre
- porte fermée
- zone d’entrée libre

### 9.2 Pendant l’ouverture

- maintenir la porte ouverte uniquement `1.5 à 2 secondes`
- détecter le passage dès `0.5 seconde` sur l’ultrason extérieur et l’ultrason intérieur
- fermer immédiatement après le passage ou si aucun passage n’est détecté

### 9.3 Scénarios frauduleux et réponses

| Cas | Protection | Action recommandée |
|---|---|---|
| Deux personnes passent à la suite | détecter 2x passage | refuser accès suivant, alerter LED/serveur |
| Personne dehors appuie sur bouton intérieur | bouton inactif pour entry | rien ne doit se passer hors sortie |
| Porte restée ouverte | notif / fermer | fermer rapidement ou alerter |
| Salle occupée mais code saisi | bloquer entrée | message "Salle occupée" |
| Autorité veut entrer en urgence | par carte magnetique | log + alerte, possible override |

---

## 10. Serveur et contrat de données

### 10.1 Endpoint code

`POST /validate_code`

Payload :
```json
{ "code": "123456" }
```

Réponse attendue :
```json
{
  "access": "pending_face" | "granted" | "denied",
  "name": "Nom Utilisateur",
  "role": "student" | "authority",
  "reason": "..."
}
```

### 10.2 Endpoint visage

`POST /verify_face`

Payload :
```json
{ "code": "123456" }
```

Réponse attendue :
```json
{
  "access": "granted" | "denied",
  "reason": "...",
  "role": "student" | "authority"
}
```

### 10.3 Champs importants

- `access` : `granted` / `denied` / `pending_face`
- `role` : distingue étudiant vs autorité
- `reason` : message pour l’utilisateur et pour les logs

### 10.4 Synchronisation serveur / ESP32

Pour éviter que l’ESP32 et le serveur aient deux états différents, chaque requête envoyée par l’ESP32 doit aussi envoyer l’état matériel :

```json
{
  "device_id": "ESP32_DOOR_01",
  "room_occupied": false,
  "door_closed": true,
  "entry_zone_clear": true
}
```

Le serveur répond avec un `session_id` quand l’accès est accordé. L’ESP32 doit ensuite confirmer ce qui s’est réellement passé :

- `POST /hardware_event` avec `event = "entry_confirmed"` si une seule personne est entrée
- `POST /hardware_event` avec `event = "passage_invalid"` si le passage est invalide ou multiple
- `POST /hardware_event` avec `event = "exit_requested"` quand le bouton intérieur est pressé
- `POST /hardware_event` avec `event = "exit_confirmed"` quand la sortie est confirmée
- `POST /hardware_event` avec `event = "state_sync"` périodiquement pour resynchroniser serveur et ESP32

Payload exemple :

```json
{
  "event": "entry_confirmed",
  "session_id": "session_retournee_par_verify_face",
  "device_id": "ESP32_DOOR_01",
  "room_occupied": true,
  "door_closed": true,
  "entry_zone_clear": true
}
```

Le serveur expose aussi `GET /status`, qui retourne l’état courant :

```json
{
  "status": "online",
  "camera": "ok",
  "room": {
    "phase": "free|await_entry|occupied|exit_requested|alert",
    "room_occupied": false,
    "door_closed": true,
    "entry_zone_clear": true
  }
}
```

### 10.5 Endpoint badge autorité

`POST /verify_badge`

Payload :

```json
{
  "badge_id": "04AABBCCDD",
  "device_id": "ESP32_DOOR_01",
  "room_occupied": true,
  "door_closed": true,
  "entry_zone_clear": true
}
```

Réponse attendue :

```json
{
  "access": "granted",
  "role": "authority",
  "name": "Nom Autorité",
  "session_id": "...",
  "override": true
}
```

Les badges peuvent être enregistrés dans une table serveur `authority_badge` ou temporairement dans `.env` via `ACCESS_AUTHORITY_BADGES=UID:Nom,UID2:Nom2`.

---

## 11. Scénario détaillé de l’usage

### 11.1 Étudiant entrant

1. l’étudiant saisit son code
2. écran : `Vérification code...`
3. code accepté, écran : `Analyse visage...`
4. visage reconnu, écran : `Accès accordé`
5. porte ouvre une très courte fenêtre
6. détection de passage unique
7. porte se referme
8. écran : `Salle occupée`

### 11.2 Étudiant sortant

1. étudiant à l’intérieur appuie sur le bouton sortie
2. système vérifie `occupé`
3. porte s’ouvre pour la sortie
4. capteur interne confirme sortie
5. porte se referme
6. état repasse à `libre`

### 11.3 Autorité

1. autorité saisit son code spécial (ou badge)
2. serveur valide le rôle `authority`
3. accès autorisé
4. log d’accès autorité
5. si nécessaire : alarme/notification supplémentaire

---

## 12. Ce qui doit être validé avant réalisation

1. choix du capteur de passage : validé avec `2 x HC-SR04`
2. choix du type de porte : `servo` vs `serrure électromécanique`
3. placement exact du bouton intérieur
4. calibration des distances pour l’ultrason extérieur et l’ultrason intérieur
5. gestion précise de l’état `occupé`
6. règles de secours si un capteur ne détecte rien
7. choix final RFID : `PN532 I2C` recommandé ou remappage SPI propre

---

## 13. Recommandation finale

Pour démarrer vite et sécurisé :

- garder le code ESP32 actuel
- utiliser deux **HC-SR04** + **reed switch porte** + **bouton intérieur**
- garder le bouton intérieur exclusivement destiné à la sortie
- utiliser une **fenêtre courte d’ouverture** et un **passage unique**
- ajouter une **barrière IR en plus** seulement si tu veux renforcer encore le comptage

---

## 14. Prochaine étape

Architecture retenue : deux ultrasons, un côté extérieur et un côté intérieur. La prochaine étape technique est de préparer :
- le schéma de câblage complet
- les pins et le câblage exact
- un diagramme d’état
- le code Arduino modifié pour ESP32
- l’adaptation serveur Python pour `role` et `access`

Ce fichier devient maintenant le cahier des charges de référence pour la partie matérielle et serveur.    

---

*Fichier généré pour analyse préliminaire avant la réalisation.*
