"""Pipeline de nettoyage : composition d'étapes, avec un journal de ce qui a été fait."""
import pandas as pd

from .etapes import Etape


class PipelineNettoyage:
    def __init__(self, etapes):
        etapes = list(etapes)
        if not etapes:
            raise ValueError("Le pipeline doit contenir au moins une étape.")
        for etape in etapes:
            if not isinstance(etape, Etape):
                raise TypeError(f"{etape!r} n'est pas une Etape.")
        self.etapes = etapes

    def __repr__(self):
        contenu = ",\n    ".join(repr(e) for e in self.etapes)
        return f"PipelineNettoyage([\n    {contenu},\n])"

    def __len__(self):
        return len(self.etapes)

    def __getitem__(self, index):
        return self.etapes[index]

    def fit(self, df, y=None):
        self.fit_transform(df, y)
        return self

    def fit_transform(self, df, y=None):
        self.journal_ = []
        for etape in self.etapes:
            avant = df
            df = etape.fit_transform(df, y)
            self.journal_.append({
                "etape": type(etape).__name__,
                "lignes": f"{len(avant)} -> {len(df)}",
                "colonnes": f"{avant.shape[1]} -> {df.shape[1]}",
                "manquants": f"{int(avant.isna().sum().sum())} -> {int(df.isna().sum().sum())}",
            })
        return df

    def transform(self, df):
        if not hasattr(self, "journal_"):
            raise RuntimeError("PipelineNettoyage n'est pas entraîné : appelez fit d'abord.")
        for etape in self.etapes:
            df = etape.transform(df)
        return df

    def journal(self):
        if not hasattr(self, "journal_"):
            raise RuntimeError("Aucun journal : appelez fit d'abord.")
        return pd.DataFrame(self.journal_)
