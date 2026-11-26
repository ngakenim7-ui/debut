# Le Data Scientist Évaluateur — ebook et données de pratique

Manuel en français pour développer les compétences d'un data scientist chargé d'**évaluer des analyses et des réponses de LLM** : qualité des données (Pandas/NumPy), statistiques et inférence, SQL avancé, visualisation, modélisation (scikit-learn, PyTorch, TensorFlow), détection des défaillances typiques des LLM et communication.

- **Lire le livre** : [`Ebook_Data_Scientist_Evaluateur.pdf`](Ebook_Data_Scientist_Evaluateur.pdf) (63 pages) ou la version [HTML](Ebook_Data_Scientist_Evaluateur.html).
- **Sources** : `chapitres/*.md` (11 chapitres + annexes).

## Démarrage rapide

```bash
cd ebook
pip install -r requirements.txt
python donnees/generer_donnees.py     # recrée les données (graine 42, résultat identique à chaque fois)
python outils/verifier_tout.py        # exécute tous les scripts et contrôle les résultats
python outils/construire_pdf.py       # reconstruit le PDF et le HTML (nécessite pandoc)
```

`verifier_tout.py --sans-deep-learning` saute PyTorch/TensorFlow si vous ne les avez pas installés.

## Contenu

| Dossier | Contenu |
|---|---|
| `chapitres/` | texte de l'ebook (Markdown) |
| `donnees/` | 7 CSV + base SQLite `pratique.db` + script de génération |
| `code/` | un script par chapitre + `exercices_corriges.py` (corrigés exécutables) |
| `sorties/` | sorties texte des scripts et figures (régénérées par `verifier_tout.py`) |
| `outils/` | vérification de bout en bout et construction du PDF |

## Jeux de données (synthétiques, avec défauts volontaires)

| Fichier | Taille | Défauts à trouver |
|---|---|---|
| `clients.csv` | 2 015 × 7 | doublons, régions mal saisies, âges aberrants, NaN |
| `transactions.csv` | 20 000 × 7 | clients orphelins, achats avant inscription |
| `produits.csv` | 40 × 4 | — |
| `churn.csv` | 5 000 × 10 | NaN, variable fuyante |
| `ab_test.csv` | 24 000 × 4 | paradoxe de Simpson |
| `ventes_mensuelles.csv` | 180 × 3 | tendance + saisonnalité |
| `immobilier.csv` | 1 500 × 7 | colinéarité |
| `pratique.db` | 5 tables | tables brutes + hiérarchie d'employés |

Environnement de vérification : Python 3.13, pandas 3.0.5, scikit-learn 1.9.1, PyTorch 2.15, TensorFlow 2.21, SQLite 3.53.
