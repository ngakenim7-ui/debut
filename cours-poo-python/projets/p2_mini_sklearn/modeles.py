"""Modèles : régression linéaire, Ridge, k plus proches voisins, régression logistique."""
import numbers

import numpy as np

from .base import BaseEstimateur, ClassifieurMixin, RegresseurMixin, verifier_X, verifier_X_y


class RegressionLineaire(RegresseurMixin, BaseEstimateur):
    """Moindres carrés ordinaires.

    Motif « méthode patron » : fit gère la validation et l'intercept (centrage),
    la résolution du système est déléguée à _resoudre, que les sous-classes redéfinissent.
    """

    def __init__(self, ajuster_intercept=True):
        self.ajuster_intercept = ajuster_intercept

    def fit(self, X, y):
        X, y = verifier_X_y(X, y)
        self._valider_hyperparametres()
        if self.ajuster_intercept:
            moyenne_X, moyenne_y = X.mean(axis=0), y.mean()
        else:
            moyenne_X, moyenne_y = np.zeros(X.shape[1]), 0.0
        # Centrer X et y permet de calculer les coefficients sans pénaliser l'intercept (utile pour Ridge)
        self.coef_ = self._resoudre(X - moyenne_X, y - moyenne_y)
        self.intercept_ = float(moyenne_y - moyenne_X @ self.coef_)
        self.n_colonnes_ = X.shape[1]
        return self

    def _valider_hyperparametres(self):
        if not isinstance(self.ajuster_intercept, bool):
            raise TypeError("ajuster_intercept doit être un booléen.")

    def _resoudre(self, X_centre, y_centre):
        coefficients, *_ = np.linalg.lstsq(X_centre, y_centre, rcond=None)
        return coefficients

    def predict(self, X):
        self._verifier_entraine()
        X = verifier_X(X)
        self._verifier_nb_colonnes(X)
        return X @ self.coef_ + self.intercept_


class RegressionRidge(RegressionLineaire):
    """Régression linéaire pénalisée : minimise ||y - Xw - b||² + alpha * ||w||²."""

    def __init__(self, alpha=1.0, ajuster_intercept=True):
        super().__init__(ajuster_intercept=ajuster_intercept)
        self.alpha = alpha

    def _valider_hyperparametres(self):
        super()._valider_hyperparametres()
        if isinstance(self.alpha, bool) or not isinstance(self.alpha, numbers.Real) or self.alpha < 0:
            raise ValueError(f"alpha doit être un nombre >= 0, reçu {self.alpha!r}.")

    def _resoudre(self, X_centre, y_centre):
        # Seule différence avec le parent : on ajoute alpha sur la diagonale de XᵀX
        n_colonnes = X_centre.shape[1]
        return np.linalg.solve(X_centre.T @ X_centre + self.alpha * np.eye(n_colonnes), X_centre.T @ y_centre)


class KPlusProchesVoisins(ClassifieurMixin, BaseEstimateur):
    """Classifieur des k plus proches voisins (distance euclidienne, vote majoritaire).

    En cas d'égalité des votes, la classe la plus petite (ordre de tri) l'emporte.
    """

    def __init__(self, k=5):
        self.k = k

    def fit(self, X, y):
        X, y = verifier_X_y(X, y, y_numerique=False)
        if isinstance(self.k, bool) or not isinstance(self.k, numbers.Integral) or self.k < 1:
            raise ValueError(f"k doit être un entier >= 1, reçu {self.k!r}.")
        if self.k > X.shape[0]:
            raise ValueError(f"k={self.k} dépasse le nombre d'exemples d'entraînement ({X.shape[0]}).")
        self.classes_, self.y_codes_ = np.unique(y, return_inverse=True)
        self.X_entrainement_ = X.copy()  # copie : l'appelant peut modifier son tableau ensuite
        self.n_colonnes_ = X.shape[1]
        return self

    def predict(self, X):
        self._verifier_entraine()
        X = verifier_X(X)
        self._verifier_nb_colonnes(X)
        # (n_test, 1, d) - (1, n_train, d) -> (n_test, n_train, d) -> distances (n_test, n_train)
        # ⚠️ mémoire en O(n_test × n_train × d) : suffisant pour apprendre, pas pour la production
        distances = ((X[:, np.newaxis, :] - self.X_entrainement_[np.newaxis, :, :]) ** 2).sum(axis=2)
        voisins = np.argsort(distances, axis=1, kind="stable")[:, : self.k]  # (n_test, k)
        codes_voisins = self.y_codes_[voisins]
        votes = np.zeros((X.shape[0], len(self.classes_)), dtype=int)
        np.add.at(votes, (np.arange(X.shape[0])[:, np.newaxis], codes_voisins), 1)
        return self.classes_[votes.argmax(axis=1)]


def _sigmoide(z):
    return 0.5 * (1.0 + np.tanh(0.5 * z))  # forme numériquement stable de 1 / (1 + exp(-z))


class RegressionLogistique(ClassifieurMixin, BaseEstimateur):
    """Classification binaire par descente de gradient (perte logistique + pénalité L2 optionnelle)."""

    def __init__(self, taux_apprentissage=0.1, nb_iterations=1000, alpha=0.0):
        self.taux_apprentissage = taux_apprentissage
        self.nb_iterations = nb_iterations
        self.alpha = alpha

    def _valider_hyperparametres(self):
        if not self.taux_apprentissage > 0:
            raise ValueError(f"taux_apprentissage doit être > 0, reçu {self.taux_apprentissage!r}.")
        if isinstance(self.nb_iterations, bool) or not isinstance(self.nb_iterations, numbers.Integral) \
                or self.nb_iterations < 1:
            raise ValueError(f"nb_iterations doit être un entier >= 1, reçu {self.nb_iterations!r}.")
        if self.alpha < 0:
            raise ValueError(f"alpha doit être >= 0, reçu {self.alpha!r}.")

    def fit(self, X, y):
        X, y = verifier_X_y(X, y, y_numerique=False)
        self._valider_hyperparametres()
        classes = np.unique(y)
        if len(classes) != 2:
            raise ValueError(f"Classification binaire uniquement : {len(classes)} classe(s) trouvée(s).")
        y01 = (y == classes[1]).astype(float)  # la 2e classe (ordre de tri) est la classe "positive"
        n, d = X.shape
        poids, biais = np.zeros(d), 0.0
        historique = []
        for _ in range(self.nb_iterations):
            p = _sigmoide(X @ poids + biais)
            p_bornee = np.clip(p, 1e-12, 1 - 1e-12)
            perte = -np.mean(y01 * np.log(p_bornee) + (1 - y01) * np.log(1 - p_bornee))
            historique.append(float(perte + 0.5 * self.alpha * poids @ poids))
            erreur = p - y01
            poids = poids - self.taux_apprentissage * (X.T @ erreur / n + self.alpha * poids)
            biais = biais - self.taux_apprentissage * erreur.mean()
        self.classes_ = classes
        self.coef_, self.intercept_ = poids, float(biais)
        self.historique_pertes_ = historique
        self.n_colonnes_ = d
        return self

    def predict_proba(self, X):
        """Renvoie un tableau (n, 2) : probabilités de classes_[0] et de classes_[1]."""
        self._verifier_entraine()
        X = verifier_X(X)
        self._verifier_nb_colonnes(X)
        p1 = _sigmoide(X @ self.coef_ + self.intercept_)
        return np.column_stack([1 - p1, p1])

    def predict(self, X):
        return self.classes_[(self.predict_proba(X)[:, 1] >= 0.5).astype(int)]
