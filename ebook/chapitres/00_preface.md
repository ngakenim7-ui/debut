# Le Data Scientist Évaluateur

## Raisonner, vérifier et critiquer : statistiques, code, modèles et réponses d'IA

*Un manuel pratique avec jeux de données, projets guidés et exercices corrigés.*

---

# Avant-propos

## À qui s'adresse ce livre

Ce livre prépare à un métier précis, qui gagne en importance : **évaluer le travail de données produit par d'autres**, et en particulier par des modèles de langage (LLM). On y attend de vous de :

- vérifier l'exactitude d'une analyse statistique ou d'une démonstration ;
- exécuter du code Python, R ou SQL pour confirmer qu'il produit ce qu'il annonce ;
- repérer les erreurs de raisonnement subtiles (paradoxe de Simpson, fuite de données, tests multiples, causalité abusive) ;
- juger la manière dont un modèle « raisonne » face à un problème de données ;
- expliquer clairement pourquoi une réponse est juste, fausse ou incomplète.

Le fil conducteur est simple : **une affirmation n'est vraie que lorsqu'elle a été vérifiée.** Chaque chiffre de ce livre a été produit par un script fourni, exécuté, et contrôlé par des assertions automatiques.

## Comment le livre est organisé

| Chapitre | Compétence travaillée | Script associé |
|---|---|---|
| 1 | La démarche de raisonnement du data scientist | — |
| 2 | Audit de qualité des données et jointures sûres (Pandas, NumPy) | `ch02_qualite_donnees.py` |
| 3 | Statistiques, inférence et pièges de raisonnement | `ch03_statistiques.py` |
| 4 | SQL avancé (CTE, fenêtrage, NULL, récursivité) | `ch04_sql.py` |
| 5 | Visualisation : lire, critiquer, construire | `ch05_visualisation.py` |
| 6 | Modélisation prédictive avec scikit-learn | `ch06_modelisation.py` |
| 7 | Deep learning avec PyTorch et TensorFlow | `ch07_deep_learning.py`, `ch07b_tensorflow.py` |
| 8 | Évaluer une réponse de LLM : méthode et cas réels | `ch08_audit_llm.py` |
| 9 | Communiquer un diagnostic | — |
| 10 | Trois projets guidés de bout en bout | `exercices_corriges.py` |
| 11 | Annexes : formulaire, check-lists, grille d'évaluation | — |

Chaque chapitre suit la même structure : **concepts → exemple commenté → raisonnement pas à pas → pièges → exercices → corrigés.**

## Installer l'environnement

```bash
git clone https://github.com/ngakenim7-ui/debut.git
cd debut/ebook
python -m venv .venv && source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python donnees/generer_donnees.py                       # recrée tous les jeux de données
python outils/verifier_tout.py                          # exécute et contrôle tous les scripts
```

Versions avec lesquelles tout a été vérifié : Python 3.13, pandas 3.0.5, NumPy, scikit-learn 1.9.1, SciPy, statsmodels, Matplotlib, PyTorch 2.15, TensorFlow 2.21, SQLite 3.53. Le code n'utilise que des API stables ; avec des versions plus anciennes, quelques fonctions peuvent manquer (par exemple `root_mean_squared_error`, apparue dans scikit-learn 1.4). PyTorch et TensorFlow ne servent qu'au chapitre 7.

## Les données de pratique

Tous les jeux sont **synthétiques, générés de façon reproductible** (graine `SEED = 42`) par `donnees/generer_donnees.py`. Relancer le script redonne des fichiers identiques octet pour octet ; `verifier_tout.py` le contrôle. Ils contiennent **volontairement des défauts** : c'est le terrain d'entraînement de votre œil critique.

| Fichier | Lignes × colonnes | Usage | Défauts volontaires |
|---|---|---|---|
| `clients.csv` | 2 015 × 7 | profils clients | 15 doublons exacts, régions mal saisies (casse, espaces), 60 âges manquants + 6 aberrants (−1, 0, 150, 200, 999, 999), 100 revenus manquants |
| `produits.csv` | 40 × 4 | catalogue | — |
| `transactions.csv` | 20 000 × 7 | ventes 2023-2024 | 150 transactions de clients inexistants, achats antérieurs à l'inscription |
| `churn.csv` | 5 000 × 10 | prédiction de résiliation | 400 satisfactions manquantes, **une variable fuyante** |
| `ab_test.csv` | 24 000 × 4 | test A/B | allocation déséquilibrée par appareil (**paradoxe de Simpson**) |
| `ventes_mensuelles.csv` | 180 × 3 | séries temporelles | tendance + saisonnalité |
| `immobilier.csv` | 1 500 × 7 | régression | forte colinéarité surface / nombre de pièces |
| `pratique.db` | 5 tables | SQL (SQLite) | données brutes non nettoyées + table `employes` hiérarchique |

> **Un mot d'honnêteté.** Les données étant simulées, nous connaissons le « vrai » mécanisme qui les a produites. C'est un avantage pédagogique : on peut vérifier si une méthode retrouve la vérité. Mais les ordres de grandeur (taux de churn, AUC, etc.) ne sont pas représentatifs d'un secteur réel. Ne les citez pas comme des références métier.

## Convention typographique

- `code` : noms de colonnes, fonctions, fichiers.
- Les blocs **« Raisonnement »** détaillent pas à pas ce qu'un data scientist se demande.
- Les blocs **« Piège »** signalent une erreur fréquente — chez les humains comme chez les LLM.
- Les blocs **« Vérifié »** rappellent la sortie exacte obtenue par le script.
