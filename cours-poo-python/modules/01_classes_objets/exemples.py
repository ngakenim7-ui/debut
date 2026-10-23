"""Module 1 — Classes et objets : exemples exécutables.

Lancez depuis le dossier cours-poo-python :
    python modules/01_classes_objets/exemples.py

Chaque section affiche un résultat ; les `assert` vérifient que ce qui est
affirmé dans le cours est vrai. Si un assert échoue, le cours est faux !
"""


class SerieDeMesures:
    """Une série de mesures numériques (relevés d'un capteur, par exemple)."""

    # Attributs de CLASSE : partagés par toutes les instances
    UNITES_VALIDES = ("°C", "%", "hPa", "m/s")
    nb_series_creees = 0

    def __init__(self, nom, unite, valeurs):
        if unite not in self.UNITES_VALIDES:
            raise ValueError(f"Unité inconnue : {unite!r}. Unités valides : {self.UNITES_VALIDES}")
        # Attributs d'INSTANCE : propres à chaque objet
        self.nom = nom
        self.unite = unite
        self.valeurs = list(valeurs)  # copie défensive
        SerieDeMesures.nb_series_creees += 1

    # --- Méthodes d'instance -------------------------------------------------
    def ajouter(self, valeur):
        self.valeurs.append(valeur)

    def moyenne(self):
        if not self.valeurs:
            raise ValueError("Impossible de calculer la moyenne d'une série vide.")
        return sum(self.valeurs) / len(self.valeurs)

    def maximum(self):
        if not self.valeurs:
            raise ValueError("Série vide.")
        return max(self.valeurs)

    # --- Méthode de classe : constructeur alternatif -------------------------
    @classmethod
    def depuis_texte(cls, nom, unite, texte, sep=";"):
        """Crée une série depuis un texte du type "21.5;22.0;23.1"."""
        valeurs = [float(v) for v in texte.split(sep) if v.strip()]
        return cls(nom, unite, valeurs)

    # --- Méthode statique : utilitaire sans état -----------------------------
    @staticmethod
    def celsius_vers_fahrenheit(celsius):
        return celsius * 9 / 5 + 32


def section(titre):
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


if __name__ == "__main__":
    section("1. Créer des objets (instances)")
    temperature = SerieDeMesures("température", "°C", [21.5, 22.0, 23.1])
    humidite = SerieDeMesures("humidité", "%", [40, 45, 50])
    temperature.ajouter(20.4)
    print("Moyenne température :", temperature.moyenne())
    print("Moyenne humidité    :", humidite.moyenne())
    assert temperature.moyenne() == 21.75
    # Chaque objet a son propre état
    assert temperature.valeurs is not humidite.valeurs

    section("2. self : s.moyenne() == Classe.moyenne(s)")
    print("temperature.moyenne()               =", temperature.moyenne())
    print("SerieDeMesures.moyenne(temperature) =", SerieDeMesures.moyenne(temperature))
    assert temperature.moyenne() == SerieDeMesures.moyenne(temperature)

    section("3. Copie défensive dans __init__")
    donnees = [1.0, 2.0, 3.0]
    s = SerieDeMesures("vent", "m/s", donnees)
    donnees.append(1000.0)  # l'appelant modifie SA liste après coup...
    print("Liste de l'appelant :", donnees)
    print("Valeurs de l'objet  :", s.valeurs, "(non affectées grâce à list(valeurs))")
    assert s.valeurs == [1.0, 2.0, 3.0]

    section("4. Attributs de classe vs d'instance")
    print("Séries créées jusqu'ici :", SerieDeMesures.nb_series_creees)
    avant = SerieDeMesures.nb_series_creees
    SerieDeMesures("pression", "hPa", [1013])
    assert SerieDeMesures.nb_series_creees == avant + 1
    # La constante de classe est accessible depuis la classe ou depuis une instance
    assert temperature.UNITES_VALIDES is SerieDeMesures.UNITES_VALIDES
    try:
        SerieDeMesures("bruit", "dB", [60])
    except ValueError as erreur:
        print("Validation dans __init__ :", erreur)

    section("5. Piège : self.compteur += 1 crée un attribut d'instance")

    class Compteur:
        total = 0

        def incrementer_mal(self):
            self.total += 1  # lit Compteur.total, puis crée self.total !

        def incrementer_bien(self):
            Compteur.total += 1

    c = Compteur()
    c.incrementer_mal()
    print("Compteur.total après incrementer_mal :", Compteur.total, "| c.total :", c.total)
    assert Compteur.total == 0 and c.total == 1 and "total" in vars(c)
    c2 = Compteur()
    c2.incrementer_bien()
    print("Compteur.total après incrementer_bien :", Compteur.total)
    assert Compteur.total == 1

    section("6. Méthodes de classe et statiques")
    s = SerieDeMesures.depuis_texte("temp", "°C", "21.5;22.0;;23.1")
    print("depuis_texte ->", s.valeurs)
    assert s.valeurs == [21.5, 22.0, 23.1]
    print("100 °C =", SerieDeMesures.celsius_vers_fahrenheit(100), "°F")
    assert SerieDeMesures.celsius_vers_fahrenheit(100) == 212.0

    section("7. Introspection")
    print("type(s)      :", type(s).__name__)
    print("isinstance   :", isinstance(s, SerieDeMesures))
    print("vars(s)      :", vars(s))
    publics = [m for m in dir(s) if not m.startswith("_")]
    print("API publique :", publics)
    assert "moyenne" in publics and "valeurs" in publics

    print("\n✅ Toutes les affirmations du module 1 sont vérifiées.")
