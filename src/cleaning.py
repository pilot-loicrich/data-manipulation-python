"""
Module de nettoyage réutilisable pour les ateliers du module PMD.
Fournit la fonction clean_sales, idempotente et journalisée (séance 3).
"""

import pandas as pd

# Colonnes descriptives à normaliser. Les identifiants (id_commande, id_client,
# id_produit, id_magasin) sont des clés : on ne les touche jamais.
TEXT_COLUMNS = ["canal", "statut", "ville_livraison"]

# Les cinq formats de date rencontrés dans ventes_brutes.csv. Ils ne se recouvrent
# pas (séparateurs et ordre différents), il n'y a donc aucune ambiguïté jour/mois.
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d %H:%M", "%d %b %Y"]


def parse_price(series):
    """Convertit une colonne de prix mixte (nombre ou texte '123,45 EUR') en float."""
    if pd.api.types.is_numeric_dtype(series):
        return series
    text = series.astype(str).str.replace(" EUR", "", regex=False)
    return pd.to_numeric(text.str.replace(",", ".", regex=False).str.strip(), errors="coerce")


def normalize_text(series):
    """Casse, espaces et accents : trois sources de faux niveaux."""
    text = series.astype(str).str.strip().str.lower()
    text = text.str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("utf-8")
    return text.str.replace(r"\s+", " ", regex=True)


def parse_dates(series):
    """Convertit une colonne de dates aux formats hétérogènes en datetime.

    Chaque format est essayé explicitement : une valeur qui n'en respecte aucun
    devient NaT au lieu d'être interprétée au hasard.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    for date_format in DATE_FORMATS:
        parsed = parsed.fillna(pd.to_datetime(series, format=date_format, errors="coerce"))
    return parsed


def iqr_bounds(series, factor=1.5):
    """Bornes de Tukey : robustes, car fondées sur des quantiles."""
    q1, q3 = series.quantile([0.25, 0.75])
    spread = q3 - q1
    return q1 - factor * spread, q3 + factor * spread


def clean_sales(df, drop_negative_quantities=True, max_quantity=None, verbose=True):
    """Nettoie le jeu de ventes et renvoie (df_propre, log).

    Étapes, dans cet ordre :
      1. copier le DataFrame reçu (ne jamais modifier l'entrée) ;
      2. convertir prix_unitaire en numérique ;
      3. normaliser les colonnes texte DESCRIPTIVES (jamais les identifiants) ;
      4. supprimer les doublons stricts ;
      5. convertir date_commande en datetime et supprimer les lignes sans date ;
      6. appliquer la stratégie retenue pour remise_pct (absence = pas de remise) ;
      7. traiter les quantités selon les paramètres ;
      8. calculer la colonne montant (net de remise).

    Chaque étape vérifie si elle a déjà été faite : réappliquer la fonction à son
    propre résultat ne change rien (idempotence).
    """
    log = {"lignes_initiales": len(df)}

    # 1. Copie : l'appelant garde ses données intactes
    df = df.copy()

    # 2. Prix
    was_missing = df["prix_unitaire"].isna().sum()
    df["prix_unitaire"] = parse_price(df["prix_unitaire"])
    log["prix_non_convertibles"] = int(df["prix_unitaire"].isna().sum() - was_missing)

    # 3. Texte descriptif. Normaliser AVANT le dédoublonnage, pour que deux lignes
    #    qui ne diffèrent que par la casse soient reconnues comme identiques.
    for column in TEXT_COLUMNS:
        before = df[column].nunique()
        df[column] = normalize_text(df[column])
        log[f"modalites_{column}"] = f"{before} -> {df[column].nunique()}"

    # 4. Doublons stricts
    n_before = len(df)
    df = df.drop_duplicates()
    log["doublons_supprimes"] = n_before - len(df)

    # 5. Dates
    df["date_commande"] = parse_dates(df["date_commande"])
    n_before = len(df)
    df = df.dropna(subset=["date_commande"])
    log["lignes_sans_date_supprimees"] = n_before - len(df)

    # 6. Remise : profils identiques avec ou sans remise (MCAR), une absence de
    #    saisie est interprétée comme une absence de remise.
    log["remises_imputees_a_zero"] = int(df["remise_pct"].isna().sum())
    df["remise_pct"] = df["remise_pct"].fillna(0.0)

    # 7. Quantités
    if drop_negative_quantities:
        n_before = len(df)
        df = df[df["quantite"] > 0]
        log["quantites_negatives_supprimees"] = n_before - len(df)
    if max_quantity is not None:
        n_before = len(df)
        df = df[df["quantite"] <= max_quantity]
        log["quantites_superieures_au_max_supprimees"] = n_before - len(df)
    # Les quantités improbables mais possibles sont conservées et signalées.
    # La borne IQR repose sur des quartiles : elle ne bouge pas d'un passage à l'autre.
    upper = iqr_bounds(df["quantite"])[1]
    df["quantite_suspecte"] = df["quantite"] > upper
    log["quantites_suspectes_signalees"] = int(df["quantite_suspecte"].sum())

    # 8. Montant net de remise
    df["montant"] = (df["quantite"] * df["prix_unitaire"] * (1 - df["remise_pct"] / 100)).round(2)

    df = df.reset_index(drop=True)
    log["lignes_finales"] = len(df)
    if verbose:
        for key, value in log.items():
            print(f"  {key:<40} {value}")
    return df, log
