"""
Module temporel réutilisable pour les ateliers du module PMD.
Conversion de dates contrôlée et détection d'anomalies de capteurs (séance 5).
"""

import pandas as pd

# Les cinq formats rencontrés dans ventes_brutes.csv. Chacun est essayé
# explicitement : aucune valeur n'est laissée à l'interprétation de pandas.
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d %H:%M", "%d %b %Y"]


def parse_dates(series, min_success_rate=0.95, formats=DATE_FORMATS):
    """Convertit une colonne de dates hétérogènes et renvoie (series_converties, report).

    Lève une ValueError si la part des valeurs renseignées effectivement converties
    est inférieure à min_success_rate : une conversion qui détruit des dates doit
    arrêter le pipeline, pas passer inaperçue.
    """
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    for date_format in formats:
        parsed = parsed.fillna(pd.to_datetime(series, format=date_format, errors="coerce"))

    n_total = len(series)
    n_already_missing = int(series.isna().sum())
    n_failed = int(parsed.isna().sum()) - n_already_missing
    n_to_convert = n_total - n_already_missing
    success_rate = (n_to_convert - n_failed) / n_to_convert if n_to_convert else 1.0

    report = {
        "n_total": n_total,
        "n_already_missing": n_already_missing,
        "n_failed": n_failed,
        "success_rate": round(success_rate, 4),
        "min_date": parsed.min(),
        "max_date": parsed.max(),
    }
    if success_rate < min_success_rate:
        raise ValueError(
            f"Taux de conversion {success_rate:.1%} inférieur au seuil {min_success_rate:.0%} : "
            f"{n_failed} valeurs non reconnues")
    return parsed, report


def find_gaps(timestamps, freq="h", min_missing=24):
    """Plages sans aucune mesure de plus de min_missing périodes.

    La série est réindexée sur la plage complète attendue (une ligne par heure) :
    les heures absentes deviennent des NaN, dont on repère les suites.
    """
    observed = pd.Series(1, index=pd.DatetimeIndex(timestamps).unique().sort_values())
    expected = pd.date_range(observed.index.min(), observed.index.max(), freq=freq)
    is_missing = observed.reindex(expected).isna()

    # Un nouveau numéro de bloc à chaque changement présent/absent
    block_id = (is_missing != is_missing.shift()).cumsum()
    missing_times = expected.to_series()[is_missing.values]
    blocks = missing_times.groupby(block_id[is_missing]).agg(["min", "max", "size"])
    blocks.columns = ["debut", "fin", "periodes_manquantes"]
    blocks = blocks[blocks["periodes_manquantes"] > min_missing].reset_index(drop=True)
    blocks["duree"] = blocks["fin"] - blocks["debut"] + pd.Timedelta(1, unit=freq)
    return blocks


def find_stuck_values(series, min_length=24):
    """Périodes où la série garde une valeur strictement constante sur plus de min_length relevés.

    Les valeurs manquantes sont retirées d'abord : un relevé absent au milieu d'un
    blocage ne doit pas couper la période en deux et la faire passer sous le seuil.
    """
    values = series.dropna().sort_index()
    block_id = (values != values.shift()).cumsum()
    blocks = values.groupby(block_id).agg(
        debut=lambda v: v.index.min(),
        fin=lambda v: v.index.max(),
        releves=lambda v: v.size,
        valeur="first",
    )
    return blocks[blocks["releves"] > min_length].reset_index(drop=True)
