"""
Module de transformation réutilisable pour les ateliers du module PMD.
Mise à l'échelle, encodage et variables dérivées (séance 4).
"""

import pandas as pd

# Variables nominales encodées en one-hot. Aucune n'est ordonnée : un encodage par
# entiers (0, 1, 2) leur inventerait un ordre et des distances qui n'existent pas.
ONE_HOT_COLUMNS = ["canal", "statut", "categorie"]
RARE_COLUMN = "sous_categorie"
RARE_THRESHOLD = 0.02
NOT_COMPLETED_STATUSES = ["annule", "retourne"]


def scale_minmax(series):
    """Ramène la série dans [0 ; 1] : (x - min) / (max - min)."""
    return (series - series.min()) / (series.max() - series.min())


def scale_zscore(series):
    """Centre sur 0 avec un écart type de 1 : (x - moyenne) / écart type."""
    return (series - series.mean()) / series.std()


def group_rare_categories(series, min_frequency=0.01, other_label="autre"):
    """Remplace les modalités plus rares que min_frequency par other_label."""
    frequencies = series.value_counts(normalize=True)
    rare_labels = frequencies[frequencies < min_frequency].index
    return series.where(~series.isin(rare_labels), other_label)


def join_products(df, products):
    """Ajoute le référentiel produits aux ventes.

    Le coût d'achat manquant est imputé par la médiane de la sous-catégorie
    (stratégie décidée en séance 3), sur le référentiel et non sur les ventes :
    un produit très vendu ne doit pas peser plus lourd dans la médiane.
    """
    products = products.copy()
    group_median = products.groupby("sous_categorie")["cout_achat"].transform("median")
    products["cout_achat"] = products["cout_achat"].fillna(group_median)
    # validate : un produit du référentiel ne doit apparaître qu'une fois,
    # sinon la jointure dupliquerait des ventes sans prévenir.
    return df.merge(products, on="id_produit", how="left", validate="many_to_one")


def add_derived_features(df):
    """Ajoute quatre variables dérivées à valeur métier."""
    df = df.copy()

    # La commande a-t-elle rapporté de l'argent ? (annulée ou retournée = non)
    df["commande_non_aboutie"] = df["statut"].isin(NOT_COMPLETED_STATUSES).astype(int)

    # Ce client dépense-t-il beaucoup en moyenne ? (segmentation, fidélisation)
    df["panier_moyen_client"] = df.groupby("id_client")["montant"].transform("mean").round(2)

    # Ce produit est-il cher pour sa catégorie ? (positionnement prix)
    category_median = df.groupby("categorie")["prix_unitaire"].transform("median")
    df["ecart_prix_median_categorie"] = (df["prix_unitaire"] / category_median - 1).round(4)

    # Que rapporte réellement la commande, remise déduite ? (rentabilité)
    net_unit_price = df["prix_unitaire"] * (1 - df["remise_pct"] / 100)
    df["marge_commande"] = (df["quantite"] * (net_unit_price - df["cout_achat"])).round(2)
    return df


def encode_categories(df, columns=ONE_HOT_COLUMNS, rare_column=RARE_COLUMN,
                      rare_threshold=RARE_THRESHOLD):
    """One-hot des colonnes nominales ; les modalités rares sont regroupées d'abord."""
    to_encode = df[columns].copy()
    to_encode[rare_column] = group_rare_categories(df[rare_column], min_frequency=rare_threshold)
    dummies = pd.get_dummies(to_encode, prefix_sep="=", dtype=int)
    return pd.concat([df.drop(columns=columns + [rare_column]), dummies], axis=1)


def prepare_features(df, products):
    """Rejoue toute la préparation de la séance 4 et renvoie un nouveau DataFrame.

    Ordre : jointure produits -> variables dérivées -> one-hot -> mise à l'échelle.
    Les variables dérivées sont calculées AVANT l'encodage, car elles ont besoin
    des colonnes texte d'origine (statut, categorie).
    """
    prepared = join_products(df.copy(), products)
    prepared = add_derived_features(prepared)
    prepared = encode_categories(prepared)
    prepared["montant_zscore"] = scale_zscore(prepared["montant"])
    return prepared
