# Rapport d’audit i18n (FR/EN)

- **Date** : 2026-03-29
- **Projet** : `MY_TFC`
- **Branche** : `main`
- **Objectif** : vérifier la couverture de traduction FR/EN sur les écrans UI.

## Périmètre audité

- Dossier : `ui/screens/**`
- Mécanisme 1 : clés i18n via `self._t(...)`
- Mécanisme 2 : traductions littérales via `translate_literal(...)`

## Méthodologie

1. Extraction automatique des clés utilisées dans les écrans.
2. Comparaison avec les dictionnaires `TRANSLATIONS["FR"]` et `TRANSLATIONS["EN"]`.
3. Audit des littéraux `translate_literal(...)` contre `LITERAL_TRANSLATIONS["EN"]`.
4. Vérification ciblée des textes de **Gestion des Accès** + formatage dynamique (`{username}`).

## Résultats

### 1) Audit des clés `_t(...)` sur `ui/screens/**`

- Fichiers scannés : **5**
- Fichiers contenant `_t(...)` : **1** (`ui/screens/admin/admin_dashboard.py`)
- Clés i18n uniques détectées : **57**
- Clés manquantes en FR : **0**
- Clés manquantes en EN : **0**

### 2) Audit des littéraux `translate_literal(...)` sur `ui/screens/**`

- Fichiers contenant `translate_literal(...)` : **1** (`ui/screens/login_screen.py`)
- Littéraux détectés : **11**
- Littéraux sans mapping EN explicite : **0**

### 3) Contrôle ciblé “Gestion des Accès”

- Vérification FR : **OK**
- Vérification EN : **OK**
- Message dynamique `delete_user_irreversible` avec `{username}` : **OK** (FR/EN)

## Conclusion

✅ La couverture i18n actuelle est **complète** pour le périmètre UI audité (FR/EN), sans clé manquante détectée.

## Recommandations

- Continuer à utiliser `self._t(...)` pour tout nouveau texte UI.
- Ajouter les clés FR/EN dans `ui/i18n/translator.py` avant intégration des nouvelles vues.
- Relancer cet audit avant chaque release majeure.
