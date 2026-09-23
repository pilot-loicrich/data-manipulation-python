"""
Module d'exploration réutilisable pour les ateliers du module PMD.
Fournit des outils d'audit et de profiling de DataFrames Pandas.
"""

import pandas as pd


def profile_dataframe(df: pd.DataFrame, name: str = "jeu de données", max_cardinality: int = 25) -> None:
    """Affiche un rapport d'exploration standard.

    Produit dans l'ordre :
      1. Le nom, les dimensions et l'empreinte mémoire ;
      2. Le nombre de lignes strictement dupliquées ;
      3. Un tableau par colonne : type, nombre de valeurs manquantes, taux en %,
         nombre de valeurs distinctes ;
      4. Les statistiques descriptives des colonnes numériques ;
      5. Pour chaque colonne texte de cardinalité inférieure à max_cardinality,
         la répartition des modalités.

    Ne renvoie rien : la fonction affiche directement.
    """
    print("=" * 70)
    print(f"RAPPORT D'EXPLORATION : {name.upper()}")
    print("=" * 70)

    # 1. Dimensions et mémoire
    mem_usage = df.memory_usage(deep=True).sum() / (1024 * 1024)
    print(f"Dimensions        : {df.shape[0]:,} lignes x {df.shape[1]} colonnes")
    print(f"Empreinte mémoire : {mem_usage:.2f} Mo")

    # 2. Lignes strictement dupliquées
    n_duplicates = df.duplicated().sum()
    pct_duplicates = (n_duplicates / len(df) * 100) if len(df) > 0 else 0
    print(f"Doublons stricts  : {n_duplicates:,} ({pct_duplicates:.2f} %)")
    print("-" * 70)

    # 3. Synthèse par colonne
    col_summary = []
    for col in df.columns:
        n_missing = df[col].isna().sum()
        pct_missing = (n_missing / len(df) * 100) if len(df) > 0 else 0
        n_unique = df[col].nunique(dropna=True)
        col_summary.append({
            "colonne": col,
            "type": str(df[col].dtype),
            "manquants": n_missing,
            "taux_manquants_%": round(pct_missing, 2),
            "valeurs_distinctes": n_unique,
        })
    summary_df = pd.DataFrame(col_summary)
    print("SYNTHÈSE DES COLONNES :")
    print(summary_df.to_string(index=False))
    print("-" * 70)

    # 4. Statistiques des colonnes numériques
    num_cols = df.select_dtypes(include=["number"]).columns
    if len(num_cols) > 0:
        print("STATISTIQUES DESCRIPTIVES (NUMÉRIQUES) :")
        print(df[num_cols].describe().round(2).to_string())
        print("-" * 70)

    # 5. Répartition des modalités pour les colonnes texte à cardinalité réduite
    text_cols = df.select_dtypes(include=["object", "string", "category"]).columns
    low_card_cols = [c for c in text_cols if df[c].nunique(dropna=True) <= max_cardinality]

    if len(low_card_cols) > 0:
        print(f"RÉPARTITIONS DES MODALITÉS (cardinalité <= {max_cardinality}) :")
        for col in low_card_cols:
            print(f"\n>> Colonne : {col} ({df[col].nunique(dropna=True)} modalités)")
            vc = df[col].value_counts(dropna=False)
            for val, count in vc.items():
                print(f"   {repr(val):<25} : {count:>6} ({count / len(df) * 100:.1f} %)")
    print("=" * 70 + "\n")
